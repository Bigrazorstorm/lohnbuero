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
    Branche, BrancheFristenprofil, BrancheFrist, Mandant,
    ChecklistItemStatus, WorkflowStatus, Ampelstatus, 
    FristenRegeltyp, WorkflowSchrittTyp, TicketPrioritaet, 
    Ticket, User
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
