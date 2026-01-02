"""
Bulk import utilities for Eternity School Evaluation System.
Handles importing staff, EOM voters, nominations, and weight matrices from Excel files.
"""
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.database import (
    Person, Cycle, EOMCycle, EOMVoter, EOMNominee, 
    Assignment, WeightMatrix, StaffSegment, EOMCategory
)
from datetime import datetime


class BulkImporter:
    """Utility class for bulk importing data from Excel files"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def import_staff_from_excel(self, file_path: str) -> Dict:
        """Import staff from Excel file (Staff_Database sheet)"""
        try:
            df = pd.read_excel(file_path, sheet_name='Staff_Database')
            
            imported = 0
            updated = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    email = row.get('Emails', '').strip()
                    if not email or pd.isna(email):
                        continue
                    
                    # Map segment
                    segment_str = str(row.get('Segment', 'whole_school')).lower().replace(' ', '_')
                    segment_map = {
                        'national': StaffSegment.NATIONAL,
                        'international': StaffSegment.INTERNATIONAL,
                        'whole_school': StaffSegment.WHOLE_SCHOOL
                    }
                    segment = segment_map.get(segment_str, StaffSegment.WHOLE_SCHOOL)
                    
                    # Check if exists
                    existing = self.db.query(Person).filter(Person.email == email).first()
                    
                    if existing:
                        # Update
                        existing.full_name = str(row.get('Name', existing.full_name))
                        existing.role_title = str(row.get('Title', existing.role_title))
                        existing.segment = segment
                        existing.active = True
                        updated += 1
                    else:
                        # Create
                        person = Person(
                            email=email,
                            full_name=str(row.get('Name', '')),
                            role_title=str(row.get('Title', '')),
                            segment=segment,
                            active=True
                        )
                        self.db.add(person)
                        imported += 1
                except Exception as e:
                    errors.append(f"Row {_ + 2}: {str(e)}")
            
            self.db.commit()
            
            return {
                'imported': imported,
                'updated': updated,
                'errors': errors[:10]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def import_eom_voters_from_excel(self, file_path: str, cycle_id: int, month: int, year: int) -> Dict:
        """Import EOM voters from Excel file"""
        try:
            df = pd.read_excel(file_path, sheet_name='Sheet1')
            
            # Get or create EOM cycle
            eom_cycle = self.db.query(EOMCycle).filter(
                EOMCycle.cycle_id == cycle_id,
                EOMCycle.month == month,
                EOMCycle.year == year
            ).first()
            
            if not eom_cycle:
                eom_cycle = EOMCycle(
                    cycle_id=cycle_id,
                    month=month,
                    year=year,
                    status='draft'
                )
                self.db.add(eom_cycle)
                self.db.flush()
            
            imported = 0
            errors = []
            
            # Handle different column structures
            email_col = None
            for col in df.columns:
                if 'email' in str(col).lower() or 'emails' in str(col).lower():
                    email_col = col
                    break
            
            if not email_col:
                return {'error': 'No email column found'}
            
            for _, row in df.iterrows():
                try:
                    email = str(row[email_col]).strip()
                    if not email or email == 'nan':
                        continue
                    
                    # Check if voter already exists
                    existing = self.db.query(EOMVoter).filter(
                        EOMVoter.eom_cycle_id == eom_cycle.id,
                        EOMVoter.voter_email == email
                    ).first()
                    
                    if not existing:
                        voter = EOMVoter(
                            eom_cycle_id=eom_cycle.id,
                            voter_email=email
                        )
                        self.db.add(voter)
                        imported += 1
                except Exception as e:
                    errors.append(f"Row {_ + 2}: {str(e)}")
            
            self.db.commit()
            
            return {
                'imported': imported,
                'eom_cycle_id': eom_cycle.id,
                'errors': errors[:10]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def import_eom_candidates_from_excel(self, file_path: str) -> Dict:
        """Import EOM candidates (potential nominees) from Excel"""
        try:
            # Try different sheet names
            sheet_name = None
            for name in ['EOM_candidates', 'Sheet1', 'EOM nom']:
                try:
                    df = pd.read_excel(file_path, sheet_name=name)
                    sheet_name = name
                    break
                except:
                    continue
            
            if not sheet_name:
                return {'error': 'Could not find EOM candidates sheet'}
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            candidates = []
            errors = []
            
            for _, row in df.iterrows():
                try:
                    email = str(row.get('Emails', '')).strip()
                    if not email or email == 'nan':
                        continue
                    
                    segment_str = str(row.get('Segment', 'whole_school')).lower().replace(' ', '_')
                    segment_map = {
                        'national': StaffSegment.NATIONAL,
                        'international': StaffSegment.INTERNATIONAL,
                        'whole_school': StaffSegment.WHOLE_SCHOOL
                    }
                    segment = segment_map.get(segment_str, StaffSegment.WHOLE_SCHOOL)
                    
                    candidates.append({
                        'email': email,
                        'name': str(row.get('Name', '')),
                        'title': str(row.get('Title', '')),
                        'segment': segment,
                        'sub_title': str(row.get('Sub Title', '')),
                        'sub_department': str(row.get('Sub Department', ''))
                    })
                except Exception as e:
                    errors.append(f"Row {_ + 2}: {str(e)}")
            
            return {
                'candidates': candidates,
                'count': len(candidates),
                'errors': errors[:10]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def import_weight_matrix_from_excel(self, file_path: str, cycle_id: int) -> Dict:
        """Import weight matrix from Excel file and create assignments"""
        try:
            df = pd.read_excel(file_path, sheet_name='Weight_Matrix')
            
            # Build matrix_config JSON structure
            matrix_config = {}
            assignments_created = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    target_group = str(row.get('target_group', ''))
                    rater_context = str(row.get('rater_context', ''))
                    evaluator_email = str(row.get('evaluator_email', ''))
                    weight = float(row.get('weight', 1.0))
                    required = bool(row.get('required', False))
                    min_count = int(row.get('min_count', 1))
                    max_count = int(row.get('max_count', 1))
                    
                    # Build nested structure: {target_group: {rater_context: {evaluator_email: weight}}}
                    if target_group not in matrix_config:
                        matrix_config[target_group] = {}
                    if rater_context not in matrix_config[target_group]:
                        matrix_config[target_group][rater_context] = {}
                    matrix_config[target_group][rater_context][evaluator_email] = {
                        'weight': weight,
                        'required': required,
                        'min_count': min_count,
                        'max_count': max_count
                    }
                except Exception as e:
                    errors.append(f"Row {_ + 2}: {str(e)}")
            
            # Create or update weight matrix
            existing = self.db.query(WeightMatrix).filter(
                WeightMatrix.cycle_id == cycle_id,
                WeightMatrix.is_active == True
            ).first()
            
            if existing:
                existing.matrix_config = matrix_config
                existing.updated_at = datetime.utcnow()
            else:
                weight_matrix = WeightMatrix(
                    cycle_id=cycle_id,
                    name=f'Weight Matrix for Cycle {cycle_id}',
                    matrix_config=matrix_config,
                    is_active=True
                )
                self.db.add(weight_matrix)
                self.db.flush()
            
            # Note: Assignment generation from weight matrix is complex and depends on
            # actual staff segments and roles. For now, we just store the matrix config.
            # Assignments can be generated separately using a dedicated function.
            assignments_created = 0
            
            self.db.commit()
            
            return {
                'imported': len(df),
                'assignments_created': assignments_created,
                'matrix_config': matrix_config,
                'errors': errors[:10]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def import_domain_weights_from_excel(self, file_path: str, cycle_id: int, target_group: str) -> Dict:
        """Import domain weights for admin or academic evaluations"""
        try:
            sheet_name = f'Domain_Weights_{target_group.capitalize()}'
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            imported = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Store domain weights in weight_matrices or separate table
                    # This is a simplified version - you may need to adjust based on your schema
                    weight_matrix = WeightMatrix(
                        cycle_id=cycle_id,
                        target_group=target_group,
                        rater_context=str(row.get('rater_context', '')),
                        domain_code=str(row.get('domain_code', '')),
                        domain_weight=float(row.get('domain_weight', 0.0))
                    )
                    self.db.add(weight_matrix)
                    imported += 1
                except Exception as e:
                    errors.append(f"Row {_ + 2}: {str(e)}")
            
            self.db.commit()
            
            return {
                'imported': imported,
                'errors': errors[:10]
            }
        except Exception as e:
            return {'error': str(e)}
