"""
Workflow Service - Advanced payroll workflow management for multi-branch operations.

Handles:
- Dynamic deadline calculation based on branch-specific rules
- Workflow SLA tracking and enforcement
- Item dependency resolution
- Ampel status computation (traffic light system)
- Automatic escalation and reminder generation
- Time tracking and performance metrics
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from sqlalchemy.orm import Session
from app.models import (
    WorkflowInstanz, WorkflowItem, WorkflowVorlage, WorkflowVorlageItem,
    WorkflowPhase, WorkflowVorlageItemDependency,
    Branche, BrancheFristenprofil, BrancheFrist, Mandant,
    ChecklistItemStatus, WorkflowStatus, Ampelstatus, 
    FristenRegeltyp, WorkflowSchrittTyp, TicketPrioritaet, 
    Ticket, User, GlobalEvent, GlobalEventSchritt, BranchenWorkflowSchritt,
    MandantWorkflowSchritt, WorkflowItemHerkunft, WorkflowSchrittEbene
)


class WorkflowService:
    """Core workflow engine for payroll processing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════
    # DEADLINE CALCULATION
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_item_deadline(
        self,
        vorlage_item: WorkflowVorlageItem,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> Optional[datetime]:
        """
        Calculate due date for a workflow item based on:
        1. Template offset (offset from month start)
        2. Fristart reference (external deadline)
        3. Mandate-specific configuration
        
        Returns: datetime or None if deadline cannot be determined
        """
        month_start = datetime(instanz.jahr, instanz.monat, 1)
        
        # Priority 1: Explicit fristart reference
        if vorlage_item.fristart_referenz:
            frist_date = self._resolve_fristart(
                vorlage_item.fristart_referenz,
                instanz,
                mandant
            )
            if frist_date:
                # Apply offset (negative = before the deadline)
                deadline = frist_date + timedelta(days=vorlage_item.fristart_offset_tage)
                return deadline
        
        # Priority 2: Template-based offset from month start
        if vorlage_item.faellig_offset_tage is not None:
            return month_start + timedelta(days=vorlage_item.faellig_offset_tage)
        
        return None
    
    def _resolve_fristart(
        self,
        fristart_ref: str,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> Optional[datetime]:
        """
        Resolve external deadline reference (e.g., "SV-Zahlung") 
        using branch-specific Fristart configuration.
        
        Example: "SV-Zahlung" → 15th of month + 2 bank working days
        """
        # Load branch fristen profile
        branche_profil = self._get_branche_profil(instanz, mandant)
        if not branche_profil:
            return None
        
        # Find matching Fristart rule
        frist_rule = self.db.query(BrancheFrist).filter(
            BrancheFrist.profil_id == branche_profil.id,
            BrancheFrist.bezeichnung == fristart_ref,
            BrancheFrist.ist_aktiv == True
        ).first()
        
        if not frist_rule:
            return None
        
        # Resolve based on rule type
        regel_config = json.loads(frist_rule.regelkonfiguration) if frist_rule.regelkonfiguration else {}
        
        if frist_rule.regeltyp == FristenRegeltyp.FIXES_DATUM:
            # E.g., {"tag": 15, "monat": 1} → 15th January
            tag = regel_config.get("tag", 1)
            monat = regel_config.get("monat", instanz.monat)
            jahr = instanz.jahr if monat >= instanz.monat else instanz.jahr + 1
            try:
                return datetime(jahr, monat, tag)
            except ValueError:
                return None
        
        elif frist_rule.regeltyp == FristenRegeltyp.RELATIV_MONATSENDE:
            # E.g., {"tage_nach_monatsende": -5} → 5 days before month end
            tage_nach = regel_config.get("tage_nach_monatsende", 0)
            next_month = datetime(instanz.jahr, instanz.monat, 1) + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
            return month_end + timedelta(days=tage_nach)
        
        elif frist_rule.regeltyp == FristenRegeltyp.RELATIV_BANKARBEITSTAGE:
            # E.g., {"bankarbeitstage_nach_zahlungsgruppe3": 1}
            # Complex - would need bankarbeitstage.py integration
            # Placeholder: just use a fixed date
            tag = regel_config.get("tag", 15)
            return datetime(instanz.jahr, instanz.monat, tag)
        
        return None
    
    def _get_branche_profil(
        self,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> Optional[BrancheFristenprofil]:
        """Get the branch-specific Fristart profile for a mandate."""
        if mandant.fristenprofil_id:
            return self.db.query(BrancheFristenprofil).filter(
                BrancheFristenprofil.id == mandant.fristenprofil_id
            ).first()
        
        # Fallback: find default profile for mandate's branch
        if mandant.branche:
            branche = self.db.query(Branche).filter(
                Branche.name == mandant.branche
            ).first()
            if branche:
                return self.db.query(BrancheFristenprofil).filter(
                    BrancheFristenprofil.branche_id == branche.id,
                    BrancheFristenprofil.ist_standard == True
                ).first()
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # AMPEL STATUS COMPUTATION
    # ═══════════════════════════════════════════════════════════════
    
    def compute_ampelstatus(self, instanz: WorkflowInstanz) -> Ampelstatus:
        """
        Compute traffic light status (traffic light) for a workflow based on:
        1. Overdue mandatory items
        2. Warning threshold (2-3 days before deadline)
        3. Critical tickets
        4. Blocked items
        """
        if instanz.status == WorkflowStatus.ABGESCHLOSSEN:
            return Ampelstatus.GRUEN
        
        now = datetime.utcnow()
        
        # Rule 1: Critical tickets blocking the workflow → Red
        kritische_tickets = self.db.query(Ticket).filter(
            Ticket.workflow_instanz_id == instanz.id,
            Ticket.prioritaet == TicketPrioritaet.KRITISCH,
            Ticket.status.in_([
                "neu", "offen", "in_bearbeitung", 
                "wartet_auf_mandant", "intern_in_klaerung"
            ])
        ).count()
        if kritische_tickets > 0:
            return Ampelstatus.ROT
        
        # Analyze open items
        open_items = [
            item for item in instanz.items
            if item.status == ChecklistItemStatus.OFFEN and item.ist_pflicht
        ]
        
        # Rule 2: Overdue mandatory items → Red
        overdue = [
            item for item in open_items
            if item.faellig_datum and item.faellig_datum < now
        ]
        if overdue:
            return Ampelstatus.ROT
        
        # Rule 3: Warning threshold (within 2-3 days of deadline) → Yellow
        warning_threshold = 2  # days
        warning_items = [
            item for item in open_items
            if item.faellig_datum and
               now <= item.faellig_datum <= now + timedelta(days=warning_threshold)
        ]
        if warning_items:
            return Ampelstatus.GELB
        
        # Rule 4: No issues → Green
        return Ampelstatus.GRUEN
    
    def update_ampel_status_with_log(self, instanz_id: int) -> Ampelstatus:
        """Compute and update ampel status, with timestamp."""
        instanz = self.db.query(WorkflowInstanz).filter(
            WorkflowInstanz.id == instanz_id
        ).first()
        
        if not instanz:
            return Ampelstatus.GRUEN
        
        new_status = self.compute_ampelstatus(instanz)
        instanz.ampelstatus = new_status
        instanz.last_ampel_update = datetime.utcnow()
        self.db.flush()
        
        return new_status
    
    # ═══════════════════════════════════════════════════════════════
    # DEPENDENCY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def check_dependencies(self, item: WorkflowItem) -> Tuple[bool, List[str]]:
        """
        Check if all dependencies of an item are satisfied.
        
        Returns: (is_unblocked, list_of_blocking_items)
        """
        if not item.abhaengig_von_items:
            return True, []
        
        dep_ids = json.loads(item.abhaengig_von_items)
        blocking_items = []
        
        for dep_id in dep_ids:
            dep_item = self.db.query(WorkflowItem).filter(
                WorkflowItem.id == dep_id,
                WorkflowItem.instanz_id == item.instanz_id
            ).first()
            
            if not dep_item or dep_item.status != ChecklistItemStatus.ERLEDIGT:
                blocking_items.append(str(dep_id))
        
        return len(blocking_items) == 0, blocking_items
    
    def auto_unblock_items(self, instanz_id: int) -> List[int]:
        """
        After completing an item, check and potentially unblock dependent items.
        Returns list of newly unblocked item IDs.
        """
        unblocked_ids = []
        
        items = self.db.query(WorkflowItem).filter(
            WorkflowItem.instanz_id == instanz_id,
            WorkflowItem.ist_blockiert == True
        ).all()
        
        for item in items:
            is_unblocked, _ = self.check_dependencies(item)
            if is_unblocked:
                item.ist_blockiert = False
                item.blockiert_grund = None
                item.blockierung_seit = None
                unblocked_ids.append(item.id)
        
        self.db.flush()
        return unblocked_ids
    
    def _apply_phase_structure(self, instanz: WorkflowInstanz) -> None:
        """
        Assign phase_id to each workflow item based on template phase assignments.
        NEW (v2.1): Phase-based workflow organization.
        """
        if not instanz.vorlage or not instanz.vorlage.phasen:
            return
        
        # Build mapping: vorlage_item_id -> phase_id
        phase_mapping = {}
        for phase in instanz.vorlage.phasen:
            for item in phase.items:
                phase_mapping[item.id] = phase.id
        
        # Assign phases to instance items
        for item in instanz.items:
            if item.vorlage_item_id and item.vorlage_item_id in phase_mapping:
                item.phase_id = phase_mapping[item.vorlage_item_id]
        
        self.db.flush()
    
    def _resolve_item_dependencies_v2(self, instanz: WorkflowInstanz) -> None:
        """
        Resolve template-level dependencies (WorkflowVorlageItemDependency)
        and apply blockages to instance items at runtime.
        NEW (v2.1): Explicit dependency model with typed relationships.
        
        Updates blockiert_von_item_ids for each item based on:
        - BLOCKIERT_VON: target item is blocked until source is FERTIG
        - MUSS_VOR: source must complete before target can be marked complete
        - PARALLEL_OK: can run in parallel
        - OPTIONAL_NACH: target is optional after source is done
        """
        if not instanz.vorlage or not instanz.vorlage.item_dependencies:
            return
        
        # Build mapping: vorlage_item_id -> instance item
        vorlage_item_to_instance = {}
        for item in instanz.items:
            if item.vorlage_item_id:
                vorlage_item_to_instance[item.vorlage_item_id] = item
        
        # Apply blocking relationships
        for dep in instanz.vorlage.item_dependencies:
            source_item = vorlage_item_to_instance.get(dep.source_item_id)
            target_item = vorlage_item_to_instance.get(dep.target_item_id)
            
            if not source_item or not target_item:
                continue
            
            # Only process BLOCKIERT_VON relationships for runtime blocking
            if dep.typ.value == "blockiert_von":
                # target is blocked by source
                current_blockers = json.loads(target_item.blockiert_von_item_ids or "[]")
                if source_item.id not in current_blockers:
                    current_blockers.append(source_item.id)
                    target_item.blockiert_von_item_ids = json.dumps(current_blockers)
                    target_item.ist_blockiert = True
                    target_item.blockiert_grund = f"Wartet auf Abschluss von: {source_item.titel}"
                    target_item.blockierung_seit = datetime.utcnow()
        
        self.db.flush()
    
    def _calculate_phase_deadlines(self, instanz: WorkflowInstanz, mandant: Mandant) -> None:
        """
        Calculate phase-level deadlines based on standard_frist_tag.
        NEW (v2.1): Each phase has an optional standard deadline.
        
        If standard_frist_tag is set (e.g., 5 = 5th of month), items in the phase
        default to that deadline unless they have explicit vorlage_item deadline.
        """
        if not instanz.vorlage or not instanz.vorlage.phasen:
            return
        
        month_start = datetime(instanz.jahr, instanz.monat, 1)
        
        for phase in instanz.vorlage.phasen:
            if not phase.standard_frist_tag:
                continue
            
            phase_deadline = month_start + timedelta(days=phase.standard_frist_tag)
            
            # Apply to items in this phase that don't have explicit deadlines
            for item in instanz.items:
                if item.phase_id == phase.id and not item.faellig_datum:
                    item.faellig_datum = phase_deadline
                    # Calculate SLA warning
                    branche_profil = self._get_branche_profil(instanz, mandant)
                    if branche_profil and branche_profil.branche:
                        warning_days = branche_profil.branche.sla_warnung_tage or 2
                        item.sla_warnung_ab = phase_deadline - timedelta(days=warning_days)
        
        self.db.flush()
    
    def _unblock_dependent_items_v2(self, completed_item: WorkflowItem) -> List[int]:
        """
        When an item is completed, unblock any items that were blocked by it.
        NEW (v2.1): Uses new blockiert_von_item_ids JSON array.
        
        Returns: List of newly unblocked item IDs
        """
        unblocked_ids = []
        
        # Find all items in the same instance that have this item in their blockiert_von list
        dependent_items = self.db.query(WorkflowItem).filter(
            WorkflowItem.instanz_id == completed_item.instanz_id,
            WorkflowItem.ist_blockiert == True,
        ).all()
        
        for item in dependent_items:
            if not item.blockiert_von_item_ids:
                continue
            
            blockers = json.loads(item.blockiert_von_item_ids)
            if completed_item.id in blockers:
                blockers.remove(completed_item.id)
                if len(blockers) == 0:
                    # All blockers are now complete
                    item.ist_blockiert = False
                    item.blockiert_von_item_ids = json.dumps([])
                    item.blockiert_grund = None
                    item.blockierung_seit = None
                    unblocked_ids.append(item.id)
                else:
                    # Still has other blockers
                    item.blockiert_von_item_ids = json.dumps(blockers)
                    # Update grund to reflect remaining blockers
                    remaining_titles = []
                    for blocker_id in blockers:
                        blocker = self.db.query(WorkflowItem).filter(
                            WorkflowItem.id == blocker_id
                        ).first()
                        if blocker:
                            remaining_titles.append(blocker.titel)
                    if remaining_titles:
                        item.blockiert_grund = f"Wartet auf Abschluss von: {', '.join(remaining_titles)}"
        
        self.db.flush()
        return unblocked_ids
    
    def _check_item_blockages(self, item: WorkflowItem) -> Tuple[bool, List[int]]:
        """
        Check if an item is currently blocked and by which items.
        NEW (v2.1): Uses new blockiert_von_item_ids JSON array.
        
        Returns: (is_blocked, list_of_blocker_ids)
        """
        if not item.blockiert_von_item_ids:
            return False, []
        
        try:
            blocker_ids = json.loads(item.blockiert_von_item_ids)
        except (json.JSONDecodeError, TypeError):
            return False, []
        
        # Filter to only incomplete blockers
        incomplete_blockers = []
        for blocker_id in blocker_ids:
            blocker = self.db.query(WorkflowItem).filter(
                WorkflowItem.id == blocker_id
            ).first()
            if blocker and blocker.status != ChecklistItemStatus.ERLEDIGT:
                incomplete_blockers.append(blocker_id)
        
        return len(incomplete_blockers) > 0, incomplete_blockers
    
    # ═══════════════════════════════════════════════════════════════
    # SLA MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_sla_deadline(
        self,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> Optional[datetime]:
        """
        Calculate overall SLA deadline for the workflow.
        Based on vorlage SLA configuration and latest critical deadline.
        """
        vorlage = instanz.vorlage
        if not vorlage or not vorlage.sla_konfiguration:
            return None
        
        sla_config = json.loads(vorlage.sla_konfiguration)
        gesamtdauer_tage = sla_config.get("gesamtdauer_tage", 30)
        
        # Calculate from workflow start or month start
        start_date = instanz.started_at or datetime(instanz.jahr, instanz.monat, 1)
        
        return start_date + timedelta(days=gesamtdauer_tage)
    
    def compute_sla_status(self, instanz: WorkflowInstanz) -> str:
        """Determine if SLA is green/yellow/red."""
        if not instanz.sla_deadline:
            return "gruen"
        
        now = datetime.utcnow()
        
        # Get SLA warning threshold from vorlage
        vorlage = instanz.vorlage
        sla_config = json.loads(vorlage.sla_konfiguration) if vorlage and vorlage.sla_konfiguration else {}
        warnung_tage = sla_config.get("warnung_tage", 5)
        
        if now > instanz.sla_deadline:
            return "rot"
        elif (instanz.sla_deadline - now).days <= warnung_tage:
            return "gelb"
        else:
            return "gruen"
    
    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW INSTANTIATION
    # ═══════════════════════════════════════════════════════════════
    
    def create_workflow_from_template(
        self,
        mandant_id: int,
        vorlage_id: Optional[int],
        monat: int,
        jahr: int,
        sachbearbeiter_id: Optional[int] = None,
        pruefer_id: Optional[int] = None,
    ) -> WorkflowInstanz:
        """
        Create a new workflow instance from a template, with calculated deadlines.
        """
        mandant = self.db.query(Mandant).filter(Mandant.id == mandant_id).first()
        if not mandant:
            raise ValueError(f"Mandant {mandant_id} not found")
        
        instanz = WorkflowInstanz(
            mandant_id=mandant_id,
            vorlage_id=vorlage_id,
            monat=monat,
            jahr=jahr,
            sachbearbeiter_id=sachbearbeiter_id or mandant.sachbearbeiter_id,
            pruefer_id=pruefer_id,
            status=WorkflowStatus.OFFEN,
            ampelstatus=Ampelstatus.GRUEN,
        )
        self.db.add(instanz)
        self.db.flush()
        
        # Load template items
        if vorlage_id:
            vorlage = self.db.query(WorkflowVorlage).filter(
                WorkflowVorlage.id == vorlage_id
            ).first()
        else:
            # Try to find matching default template
            vorlage = self._find_suitable_template(mandant, monat, jahr)
        
        if vorlage:
            self._populate_workflow_items(instanz, vorlage, mandant)
        
        # Add branch-specific steps
        self._add_branchen_schritte(instanz, mandant)
        
        # Add mandant-specific steps
        self._add_mandant_schritte(instanz, mandant)
        
        # Add global event steps (Jahreswechsel, Mindestlohnerhöhung, etc.)
        self._add_global_event_schritte(instanz, mandant, monat, jahr)
        
        # Re-calculate positions after adding all steps
        self._recalculate_positions(instanz)
        
        # NEW (v2.1): Apply phase structure and resolve dependencies
        if vorlage:
            self._apply_phase_structure(instanz)
            self._resolve_item_dependencies_v2(instanz)
            self._calculate_phase_deadlines(instanz, mandant)
        
        # Calculate SLA deadline
        instanz.sla_deadline = self.calculate_sla_deadline(instanz, mandant)
        
        self.db.flush()
        return instanz
    
    def _find_suitable_template(
        self,
        mandant: Mandant,
        monat: int,
        jahr: int
    ) -> Optional[WorkflowVorlage]:
        """Find best-matching workflow template for a mandate."""
        # Priority: branche match + kategorie + standard
        templates = self.db.query(WorkflowVorlage).filter(
            WorkflowVorlage.ist_onboarding == False,
            WorkflowVorlage.is_archiviert == False,
        ).order_by(
            # Exact branch match
            (WorkflowVorlage.branche_id != None).desc(),
            (WorkflowVorlage.kategorie == mandant.kategorie).desc(),
            WorkflowVorlage.ist_standard.desc(),
        ).first()
        
        return templates
    
    def _populate_workflow_items(
        self,
        instanz: WorkflowInstanz,
        vorlage: WorkflowVorlage,
        mandant: Mandant
    ) -> None:
        """Create workflow items from template items with calculated deadlines."""
        # Parse mandate-specific optional items configuration
        optional_items_config = {}
        if mandant.workflow_konfiguration:
            config = json.loads(mandant.workflow_konfiguration)
            optional_items_config = config.get("vorlage_item_ids", {})
        
        for idx, vorlage_item in enumerate(vorlage.items, start=1):
            # Skip optional items not enabled for this mandate
            if vorlage_item.ist_optional_pro_mandant:
                if vorlage_item.id not in optional_items_config:
                    continue
            
            # Calculate deadline
            deadline = self.calculate_item_deadline(vorlage_item, instanz, mandant)
            
            # Calculate SLA warning threshold
            sla_warning = None
            if deadline:
                branche_profil = self._get_branche_profil(instanz, mandant)
                if branche_profil and branche_profil.branche:
                    warning_days = branche_profil.branche.sla_warnung_tage or 2
                    sla_warning = deadline - timedelta(days=warning_days)
            
            item = WorkflowItem(
                instanz_id=instanz.id,
                vorlage_item_id=vorlage_item.id,
                position=idx,
                titel=vorlage_item.titel,
                beschreibung=vorlage_item.beschreibung,
                schritttyp=vorlage_item.schritttyp,
                verantwortlich_rolle=vorlage_item.verantwortlich_rolle,
                faellig_datum=deadline,
                sla_warnung_ab=sla_warning,
                ist_pflicht=vorlage_item.ist_pflicht,
                erfordert_dokument=vorlage_item.erfordert_dokument,
                erfordert_pruefung=vorlage_item.erfordert_pruefung,
                fristart_referenz=vorlage_item.fristart_referenz,
                abhaengig_von_items=vorlage_item.abhaengig_von_items,
                punkte=vorlage_item.standard_punkte,
                status=ChecklistItemStatus.OFFEN,
            )
            self.db.add(item)
            self.db.flush()
            
            # Track source (Herkunft) of this item
            herkunft = WorkflowItemHerkunft(
                workflow_item_id=item.id,
                ebene=WorkflowSchrittEbene.STANDARD,
                vorlage_item_id=vorlage_item.id
            )
            self.db.add(herkunft)
        
        self.db.flush()
    
    def _add_branchen_schritte(
        self,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> None:
        """Add branch-specific workflow steps for the mandate's branch."""
        from datetime import datetime as dt
        now = dt.utcnow()
        
        # Get all branches for this mandate
        branche_ids = [b.id for b in mandant.branchen_liste] if mandant.branchen_liste else []
        
        # Also try to match by branche name
        if mandant.branche:
            branche = self.db.query(Branche).filter(
                Branche.name == mandant.branche,
                Branche.ist_aktiv == True
            ).first()
            if branche and branche.id not in branche_ids:
                branche_ids.append(branche.id)
        
        if not branche_ids:
            return
        
        # Get active branch-specific steps
        branchen_schritte = self.db.query(BranchenWorkflowSchritt).filter(
            BranchenWorkflowSchritt.branche_id.in_(branche_ids),
            BranchenWorkflowSchritt.ist_aktiv == True,
            (BranchenWorkflowSchritt.gueltig_von == None) | (BranchenWorkflowSchritt.gueltig_von <= now),
            (BranchenWorkflowSchritt.gueltig_bis == None) | (BranchenWorkflowSchritt.gueltig_bis >= now)
        ).order_by(BranchenWorkflowSchritt.branche_id, BranchenWorkflowSchritt.position).all()
        
        # Check if any optional steps are disabled for this mandate
        disabled_steps = set()
        if mandant.workflow_konfiguration:
            config = json.loads(mandant.workflow_konfiguration)
            disabled_steps = set(config.get("disabled_branchen_schritte", []))
        
        max_position = max([item.position for item in instanz.items], default=0)
        
        for schritt in branchen_schritte:
            # Skip if optional and disabled for this mandate
            if schritt.ist_optional_pro_mandant and schritt.id in disabled_steps:
                continue
            
            # Calculate deadline
            deadline = self._calculate_schritt_deadline(schritt, instanz, mandant)
            sla_warning = deadline - timedelta(days=2) if deadline else None
            
            max_position += 1
            item = WorkflowItem(
                instanz_id=instanz.id,
                position=max_position,
                titel=f"[{mandant.branche}] {schritt.titel}",
                beschreibung=schritt.beschreibung,
                schritttyp=schritt.schritttyp,
                verantwortlich_rolle=schritt.verantwortlich_rolle,
                faellig_datum=deadline,
                sla_warnung_ab=sla_warning,
                ist_pflicht=schritt.ist_pflicht,
                erfordert_dokument=schritt.erfordert_dokument,
                erfordert_pruefung=schritt.erfordert_pruefung,
                fristart_referenz=schritt.fristart_referenz,
                punkte=schritt.standard_punkte,
                status=ChecklistItemStatus.OFFEN,
            )
            self.db.add(item)
            self.db.flush()
            
            # Track source
            herkunft = WorkflowItemHerkunft(
                workflow_item_id=item.id,
                ebene=WorkflowSchrittEbene.BRANCHE,
                branchen_schritt_id=schritt.id
            )
            self.db.add(herkunft)
        
        self.db.flush()
    
    def _add_mandant_schritte(
        self,
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> None:
        """Add mandant-specific workflow steps."""
        from datetime import datetime as dt
        now = dt.utcnow()
        
        # Get active mandant-specific steps
        mandant_schritte = self.db.query(MandantWorkflowSchritt).filter(
            MandantWorkflowSchritt.mandant_id == mandant.id,
            MandantWorkflowSchritt.ist_aktiv == True,
            (MandantWorkflowSchritt.aenderung_zum == None) | (MandantWorkflowSchritt.aenderung_zum <= now)
        ).all()
        
        max_position = max([item.position for item in instanz.items], default=0)
        
        for mws in mandant_schritte:
            schritt_typ = mws.schritt_typ
            if not schritt_typ or not schritt_typ.ist_aktiv:
                continue
            
            # Calculate deadline from schritt_typ configuration
            deadline = None
            if schritt_typ.fristart_referenz:
                # Try to resolve the deadline reference
                deadline = self._resolve_fristart(
                    schritt_typ.fristart_referenz, instanz, mandant
                )
                if deadline and schritt_typ.fristart_offset_tage:
                    deadline = deadline + timedelta(days=schritt_typ.fristart_offset_tage)
            
            sla_warning = deadline - timedelta(days=2) if deadline else None
            
            max_position += 1
            item = WorkflowItem(
                instanz_id=instanz.id,
                position=max_position,
                titel=f"[Spezifisch] {schritt_typ.name}",
                beschreibung=schritt_typ.beschreibung,
                verantwortlich_rolle=schritt_typ.standard_rolle,
                faellig_datum=deadline,
                sla_warnung_ab=sla_warning,
                ist_pflicht=schritt_typ.ist_pflicht,
                punkte=schritt_typ.standard_punkte,
                status=ChecklistItemStatus.OFFEN,
            )
            self.db.add(item)
            self.db.flush()
            
            # Track source
            herkunft = WorkflowItemHerkunft(
                workflow_item_id=item.id,
                ebene=WorkflowSchrittEbene.MANDANT,
                mandant_schritt_id=mws.id
            )
            self.db.add(herkunft)
        
        self.db.flush()
    
    def _add_global_event_schritte(
        self,
        instanz: WorkflowInstanz,
        mandant: Mandant,
        monat: int,
        jahr: int
    ) -> None:
        """Add workflow steps from active global events (Jahreswechsel, etc.)."""
        from datetime import datetime as dt
        now = dt.utcnow()
        
        # Find active global events for this month/year
        events = self.db.query(GlobalEvent).filter(
            GlobalEvent.ist_aktiv == True,
            GlobalEvent.ist_abgeschlossen == False,
            GlobalEvent.gueltig_von <= now,
            (GlobalEvent.gueltig_bis == None) | (GlobalEvent.gueltig_bis >= now),
            # Filter by tenant if applicable
            (GlobalEvent.tenant_id == None) | (GlobalEvent.tenant_id == mandant.tenant_id)
        ).all()
        
        matching_events = []
        for event in events:
            if self._event_applies_to_month(event, monat, jahr) and \
               self._event_applies_to_mandant(event, mandant):
                matching_events.append(event)
                # Link event to workflow instance
                instanz.global_events.append(event)
        
        max_position = max([item.position for item in instanz.items], default=0)
        
        for event in matching_events:
            for schritt in sorted(event.schritte, key=lambda s: s.position):
                if not schritt.ist_aktiv:
                    continue
                
                # Calculate deadline
                deadline = self._calculate_schritt_deadline(schritt, instanz, mandant)
                sla_warning = deadline - timedelta(days=2) if deadline else None
                
                max_position += 1
                item = WorkflowItem(
                    instanz_id=instanz.id,
                    position=max_position,
                    titel=f"[{event.name}] {schritt.titel}",
                    beschreibung=schritt.beschreibung or schritt.anleitung,
                    schritttyp=schritt.schritttyp,
                    verantwortlich_rolle=schritt.verantwortlich_rolle,
                    faellig_datum=deadline,
                    sla_warnung_ab=sla_warning,
                    ist_pflicht=schritt.ist_pflicht,
                    erfordert_dokument=schritt.erfordert_dokument,
                    erfordert_pruefung=schritt.erfordert_pruefung,
                    fristart_referenz=schritt.fristart_referenz,
                    punkte=schritt.standard_punkte,
                    status=ChecklistItemStatus.OFFEN,
                )
                self.db.add(item)
                self.db.flush()
                
                # Track source
                herkunft = WorkflowItemHerkunft(
                    workflow_item_id=item.id,
                    ebene=WorkflowSchrittEbene.GLOBAL_EVENT,
                    global_event_schritt_id=schritt.id
                )
                self.db.add(herkunft)
        
        self.db.flush()
    
    def _event_applies_to_month(self, event: GlobalEvent, monat: int, jahr: int) -> bool:
        """Check if an event applies to a specific month/year."""
        if not event.betroffene_monate:
            return True  # No filter = applies to all
        
        try:
            monate = json.loads(event.betroffene_monate)
            for m in monate:
                if m.get("monat") == monat and m.get("jahr") == jahr:
                    return True
            return False
        except (json.JSONDecodeError, TypeError):
            return True
    
    def _event_applies_to_mandant(self, event: GlobalEvent, mandant: Mandant) -> bool:
        """Check if an event applies to a specific mandant."""
        if not event.mandanten_filter:
            return True  # No filter = applies to all
        
        try:
            filter_config = json.loads(event.mandanten_filter)
            
            # Check "alle" flag
            if filter_config.get("alle", False):
                return True
            
            # Check branch filter
            if "branchen" in filter_config:
                mandant_branchen = [mandant.branche] if mandant.branche else []
                mandant_branchen.extend([b.name for b in mandant.branchen_liste])
                if not any(b in filter_config["branchen"] for b in mandant_branchen):
                    return False
            
            # Check category filter
            if "kategorien" in filter_config:
                if mandant.kategorie and mandant.kategorie.value not in filter_config["kategorien"]:
                    return False
            
            return True
        except (json.JSONDecodeError, TypeError):
            return True
    
    def _calculate_schritt_deadline(
        self,
        schritt,  # BranchenWorkflowSchritt or GlobalEventSchritt
        instanz: WorkflowInstanz,
        mandant: Mandant
    ) -> Optional[datetime]:
        """Calculate deadline for a branch or global event step."""
        month_start = datetime(instanz.jahr, instanz.monat, 1)
        
        # Priority 1: Fristart reference
        if hasattr(schritt, 'fristart_referenz') and schritt.fristart_referenz:
            frist_date = self._resolve_fristart(
                schritt.fristart_referenz, instanz, mandant
            )
            if frist_date:
                offset = getattr(schritt, 'fristart_offset_tage', 0) or 0
                return frist_date + timedelta(days=offset)
        
        # Priority 2: Offset from month start
        offset = getattr(schritt, 'faellig_offset_tage', 0) or 0
        return month_start + timedelta(days=offset)
    
    def _recalculate_positions(self, instanz: WorkflowInstanz) -> None:
        """Recalculate positions of all items, sorting by original position and insert position."""
        items = sorted(instanz.items, key=lambda x: x.position)
        for idx, item in enumerate(items, start=1):
            item.position = idx
        self.db.flush()
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDATION & CLOSING
    # ═══════════════════════════════════════════════════════════════
    
    def validate_can_close(self, instanz: WorkflowInstanz) -> Tuple[bool, List[str]]:
        """
        Validate if a workflow can be closed (Monatsabschluss).
        Returns: (can_close, list_of_errors)
        """
        errors = []
        
        # 1. All mandatory items must be completed
        open_pflicht = [
            i for i in instanz.items
            if i.ist_pflicht and i.status != ChecklistItemStatus.ERLEDIGT
        ]
        if open_pflicht:
            errors.append(
                f"{len(open_pflicht)} Pflicht-Schritte noch nicht erledigt: " +
                ", ".join([i.titel for i in open_pflicht[:3]])
            )
        
        # 2. If prüfer assigned, 4-eyes must be done
        if instanz.pruefer_id and not instanz.probe_geprueft_am:
            errors.append("4-Augen-Prüfung noch nicht abgeschlossen")
        
        # 3. No critical tickets open
        kritische_tickets = self.db.query(Ticket).filter(
            Ticket.mandant_id == instanz.mandant_id,
            Ticket.monat == instanz.monat,
            Ticket.jahr == instanz.jahr,
            Ticket.prioritaet == TicketPrioritaet.KRITISCH,
            Ticket.status.in_(["neu", "offen", "in_bearbeitung", "wartet_auf_mandant"])
        ).count()
        if kritische_tickets:
            errors.append(f"{kritische_tickets} kritische Ticket(s) noch offen")
        
        # 4. No blocked items
        blocked_items = [i for i in instanz.items if i.ist_blockiert]
        if blocked_items:
            errors.append(
                f"{len(blocked_items)} Schritt(e) blockiert: " +
                ", ".join([i.titel for i in blocked_items[:3]])
            )
        
        return len(errors) == 0, errors
    
    # ═══════════════════════════════════════════════════════════════
    # REPORTING & METRICS
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_metrics(self, instanz: WorkflowInstanz) -> Dict[str, Any]:
        """Calculate performance metrics for a workflow."""
        items = instanz.items
        now = datetime.utcnow()
        
        completed = [i for i in items if i.status == ChecklistItemStatus.ERLEDIGT]
        open_items = [i for i in items if i.status == ChecklistItemStatus.OFFEN]
        
        # Time metrics
        durchlaufzeit = None
        if instanz.abgeschlossen_am and instanz.created_at:
            durchlaufzeit = (instanz.abgeschlossen_am - instanz.created_at).total_seconds() / 3600
        
        # Calculate delays
        overdue_days = 0
        if instanz.sla_deadline and instanz.abgeschlossen_am:
            if instanz.abgeschlossen_am > instanz.sla_deadline:
                overdue_days = (instanz.abgeschlossen_am - instanz.sla_deadline).days
        
        return {
            "items_gesamt": len(items),
            "items_erledigt": len(completed),
            "items_offen": len(open_items),
            "prozent_fertig": (len(completed) / len(items) * 100) if items else 0,
            "durchlaufzeit_stunden": durchlaufzeit,
            "verzoegerung_tage": overdue_days,
            "punkte": instanz.punkte,
            "ampel": instanz.ampelstatus.value if instanz.ampelstatus else None,
        }
