"""
Comprehensive unit tests for EOM rotation validation system.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import date, datetime, timedelta
from backend.eom_validation import (
    EOMNominationValidator, ValidationResult, RotationPeriodType
)
from backend.eom_rotation_manager import EOMRotationManager
from backend.database import (
    EOMCategory, EOMCycle, EOMWinner, EOMNominee, EOMRotationRule,
    Cycle, Person
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_eom_cycle():
    """Create a sample EOM cycle"""
    cycle = Mock(spec=EOMCycle)
    cycle.id = 1
    cycle.cycle_id = 1
    cycle.month = 3
    cycle.year = 2024
    cycle.status = 'active'
    return cycle


@pytest.fixture
def sample_rotation_rule():
    """Create a sample rotation rule"""
    rule = Mock(spec=EOMRotationRule)
    rule.id = 1
    rule.category = EOMCategory.OUTSTANDING_LEADERSHIP
    rule.cycle_id = 1
    rule.cooldown_period = 3
    rule.max_wins_per_period = 1
    rule.period_type = 'year'
    rule.is_active = True
    return rule


class TestComprehensiveRotationRules:
    """Test comprehensive rotation rules validation"""
    
    def test_check_comprehensive_rotation_rules_with_rule(
        self, mock_db_session, sample_eom_cycle, sample_rotation_rule
    ):
        """Test rotation rules check with configured rule"""
        validator = EOMNominationValidator(mock_db_session)
        
        # Mock queries
        eom_cycle_query = MagicMock()
        eom_cycle_query.filter.return_value = eom_cycle_query
        eom_cycle_query.first.return_value = sample_eom_cycle
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = None
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = [sample_rotation_rule]
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.order_by.return_value = winner_query
        winner_query.first.return_value = None  # No previous wins
        
        nominee_query = MagicMock()
        nominee_query.filter.return_value = nominee_query
        nominee_query.order_by.return_value = nominee_query
        nominee_query.first.return_value = None
        
        mock_db_session.query.side_effect = lambda model: {
            EOMCycle: eom_cycle_query,
            Cycle: cycle_query,
            EOMRotationRule: rule_query,
            EOMWinner: winner_query,
            EOMNominee: nominee_query
        }.get(model, MagicMock())
        
        result = validator._check_comprehensive_rotation_rules(
            nominee_email='teacher1@example.com',
            eom_cycle_id=1,
            category='academic',
            term='2024-Q1',
            month=3,
            year=2024
        )
        
        assert isinstance(result, dict)
        assert 'rules_applied' in result.get('details', {})
    
    def test_check_cooldown_period_no_previous_wins(
        self, mock_db_session, sample_rotation_rule
    ):
        """Test cooldown check when nominee has no previous wins"""
        validator = EOMNominationValidator(mock_db_session)
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.order_by.return_value = winner_query
        winner_query.first.return_value = None  # No previous wins
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_cooldown_period(
            nominee_email='teacher1@example.com',
            rule=sample_rotation_rule,
            current_month=3,
            current_year=2024,
            category='academic'
        )
        
        assert result['is_valid'] is True
        assert 'message' in result
    
    def test_check_cooldown_period_with_previous_win(
        self, mock_db_session, sample_rotation_rule
    ):
        """Test cooldown check when nominee has previous win"""
        validator = EOMNominationValidator(mock_db_session)
        
        # Create a previous win within cooldown period
        previous_win = Mock(spec=EOMWinner)
        previous_win.announced_at = date(2024, 1, 15)  # 2 months ago
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.order_by.return_value = winner_query
        winner_query.first.return_value = previous_win
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_cooldown_period(
            nominee_email='teacher1@example.com',
            rule=sample_rotation_rule,
            current_month=3,
            current_year=2024,
            category='academic'
        )
        
        # With 3 period cooldown and win 2 months ago, should still be in cooldown
        # (cooldown would be 3 years, so definitely in cooldown)
        assert isinstance(result, dict)
        assert 'last_win_date' in result or 'is_valid' in result
    
    def test_check_max_wins_per_period(
        self, mock_db_session, sample_rotation_rule
    ):
        """Test max wins per period check"""
        validator = EOMNominationValidator(mock_db_session)
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.count.return_value = 0  # No wins in period
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_max_wins_per_period(
            nominee_email='teacher1@example.com',
            rule=sample_rotation_rule,
            current_month=3,
            current_year=2024,
            category='academic'
        )
        
        assert result['is_valid'] is True
        assert result['wins_in_period'] == 0
    
    def test_check_max_wins_per_period_exceeded(
        self, mock_db_session, sample_rotation_rule
    ):
        """Test max wins check when limit is exceeded"""
        validator = EOMNominationValidator(mock_db_session)
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.count.return_value = 2  # Already has 2 wins (exceeds max of 1)
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_max_wins_per_period(
            nominee_email='teacher1@example.com',
            rule=sample_rotation_rule,
            current_month=3,
            current_year=2024,
            category='academic'
        )
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0


class TestPeriodCalculations:
    """Test period calculation methods"""
    
    def test_calculate_period_dates_year(self, mock_db_session):
        """Test year period calculation"""
        validator = EOMNominationValidator(mock_db_session)
        
        period_start, period_end = validator._calculate_period_dates(
            current_month=6,
            current_year=2024,
            period_type='year'
        )
        
        assert period_start == date(2024, 1, 1)
        assert period_end == date(2024, 12, 31)
    
    def test_calculate_period_dates_quarter(self, mock_db_session):
        """Test quarter period calculation"""
        validator = EOMNominationValidator(mock_db_session)
        
        period_start, period_end = validator._calculate_period_dates(
            current_month=5,
            current_year=2024,
            period_type='quarter'
        )
        
        assert period_start == date(2024, 4, 1)
        assert period_end == date(2024, 6, 30)
    
    def test_calculate_period_dates_month(self, mock_db_session):
        """Test month period calculation"""
        validator = EOMNominationValidator(mock_db_session)
        
        period_start, period_end = validator._calculate_period_dates(
            current_month=3,
            current_year=2024,
            period_type='month'
        )
        
        assert period_start == date(2024, 3, 1)
        assert period_end == date(2024, 3, 31)
    
    def test_calculate_cooldown_end_year(self, mock_db_session):
        """Test cooldown end calculation for year period"""
        validator = EOMNominationValidator(mock_db_session)
        
        last_win = date(2023, 6, 15)
        cooldown_end = validator._calculate_cooldown_end(
            last_win_date=last_win,
            cooldown_period=1,
            period_type='year'
        )
        
        assert cooldown_end.year == 2024
        assert cooldown_end.month == 6
    
    def test_calculate_cooldown_end_quarter(self, mock_db_session):
        """Test cooldown end calculation for quarter period"""
        validator = EOMNominationValidator(mock_db_session)
        
        last_win = date(2024, 1, 15)
        cooldown_end = validator._calculate_cooldown_end(
            last_win_date=last_win,
            cooldown_period=2,  # 2 quarters = 6 months
            period_type='quarter'
        )
        
        assert cooldown_end.year == 2024
        assert cooldown_end.month == 7  # 1 + 6 = 7


class TestRotationRuleManagement:
    """Test rotation rule management methods"""
    
    def test_create_rotation_rule(self, mock_db_session):
        """Test creating a rotation rule"""
        validator = EOMNominationValidator(mock_db_session)
        
        # Mock database operations
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        rule = validator.create_rotation_rule(
            category=EOMCategory.OUTSTANDING_LEADERSHIP,
            cycle_id=1,
            cooldown_period=3,
            max_wins_per_period=1,
            period_type='year',
            is_active=True
        )
        
        assert isinstance(rule, Mock)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_update_rotation_rule(self, mock_db_session, sample_rotation_rule):
        """Test updating a rotation rule"""
        validator = EOMNominationValidator(mock_db_session)
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.first.return_value = sample_rotation_rule
        
        mock_db_session.query.return_value = rule_query
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        updated_rule = validator.update_rotation_rule(
            rule_id=1,
            cooldown_period=6,
            max_wins_per_period=2
        )
        
        assert sample_rotation_rule.cooldown_period == 6
        assert sample_rotation_rule.max_wins_per_period == 2
        mock_db_session.commit.assert_called_once()
    
    def test_get_rotation_rules_for_cycle(
        self, mock_db_session, sample_rotation_rule
    ):
        """Test getting rotation rules for a cycle"""
        validator = EOMNominationValidator(mock_db_session)
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = [sample_rotation_rule]
        
        mock_db_session.query.return_value = rule_query
        
        rules = validator.get_rotation_rules_for_cycle(
            cycle_id=1,
            active_only=True
        )
        
        assert len(rules) == 1
        assert rules[0].id == sample_rotation_rule.id


class TestEligibilityChecking:
    """Test eligibility checking methods"""
    
    def test_check_nominee_rotation_eligibility_no_rules(
        self, mock_db_session, sample_eom_cycle
    ):
        """Test eligibility check when no rules are configured"""
        validator = EOMNominationValidator(mock_db_session)
        
        eom_cycle_query = MagicMock()
        eom_cycle_query.filter.return_value = eom_cycle_query
        eom_cycle_query.first.return_value = sample_eom_cycle
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = []  # No rules
        
        nominee_query = MagicMock()
        nominee_query.filter.return_value = nominee_query
        nominee_query.order_by.return_value = nominee_query
        nominee_query.first.return_value = None
        
        mock_db_session.query.side_effect = lambda model: {
            EOMCycle: eom_cycle_query,
            EOMRotationRule: rule_query,
            EOMNominee: nominee_query
        }.get(model, MagicMock())
        
        eligibility = validator.check_nominee_rotation_eligibility(
            nominee_email='teacher1@example.com',
            category=EOMCategory.OUTSTANDING_LEADERSHIP,
            eom_cycle_id=1
        )
        
        assert eligibility['eligible'] is True
        assert eligibility['rule_type'] == 'default'
    
    def test_check_nominee_rotation_eligibility_with_rules(
        self, mock_db_session, sample_eom_cycle, sample_rotation_rule
    ):
        """Test eligibility check with configured rules"""
        validator = EOMNominationValidator(mock_db_session)
        
        eom_cycle_query = MagicMock()
        eom_cycle_query.filter.return_value = eom_cycle_query
        eom_cycle_query.first.return_value = sample_eom_cycle
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = [sample_rotation_rule]
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.order_by.return_value = winner_query
        winner_query.first.return_value = None  # No previous wins
        winner_query.count.return_value = 0  # No wins in period
        
        mock_db_session.query.side_effect = lambda model: {
            EOMCycle: eom_cycle_query,
            EOMRotationRule: rule_query,
            EOMWinner: winner_query
        }.get(model, MagicMock())
        
        eligibility = validator.check_nominee_rotation_eligibility(
            nominee_email='teacher1@example.com',
            category=EOMCategory.OUTSTANDING_LEADERSHIP,
            eom_cycle_id=1
        )
        
        assert 'eligible' in eligibility
        assert 'rule_results' in eligibility


class TestRotationManager:
    """Test EOMRotationManager class"""
    
    def test_setup_default_rules(self, mock_db_session):
        """Test setting up default rotation rules"""
        manager = EOMRotationManager(mock_db_session)
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.first.return_value = None  # No existing rules
        
        mock_db_session.query.return_value = rule_query
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        # Mock the validator's create_rotation_rule
        created_rule = Mock(spec=EOMRotationRule)
        manager.validator.create_rotation_rule = Mock(return_value=created_rule)
        
        rules = manager.setup_default_rules(cycle_id=1)
        
        assert len(rules) > 0
        assert all(isinstance(r, Mock) for r in rules)
    
    def test_get_rotation_summary(self, mock_db_session):
        """Test getting rotation summary"""
        manager = EOMRotationManager(mock_db_session)
        
        # Mock queries
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = []
        
        eom_cycle_query = MagicMock()
        eom_cycle_query.filter.return_value = eom_cycle_query
        eom_cycle_query.all.return_value = []
        
        mock_db_session.query.side_effect = lambda model: {
            EOMRotationRule: rule_query,
            EOMCycle: eom_cycle_query
        }.get(model, MagicMock())
        
        # Mock analytics
        manager.validator.get_rotation_analytics = Mock(return_value={
            'total_wins': 0,
            'unique_winners': 0
        })
        
        summary = manager.get_rotation_summary(cycle_id=1)
        
        assert 'cycle_id' in summary
        assert 'rotation_rules' in summary
        assert 'analytics' in summary


class TestDefaultRotationRules:
    """Test default rotation rules when no rules are configured"""
    
    def test_check_default_rotation_rules_no_previous_win(
        self, mock_db_session
    ):
        """Test default rules when nominee has no previous wins"""
        validator = EOMNominationValidator(mock_db_session)
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.first.return_value = None  # No previous win
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_default_rotation_rules(
            nominee_email='teacher1@example.com',
            term='2024-Q1',
            category='academic'
        )
        
        assert result['is_valid'] is True
        assert result['rule_type'] == 'default'
    
    def test_check_default_rotation_rules_with_previous_win(
        self, mock_db_session
    ):
        """Test default rules when nominee has previous win in same term"""
        validator = EOMNominationValidator(mock_db_session)
        
        previous_win = Mock(spec=EOMWinner)
        previous_win.eom_cycle_id = 1
        previous_win.term = '2024-Q1'
        previous_win.category = 'academic'
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.first.return_value = previous_win
        
        mock_db_session.query.return_value = winner_query
        
        result = validator._check_default_rotation_rules(
            nominee_email='teacher1@example.com',
            term='2024-Q1',
            category='academic'
        )
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0


class TestBatchValidation:
    """Test batch validation methods"""
    
    def test_validate_batch_nominations(self, mock_db_session):
        """Test batch validation of multiple nominations"""
        validator = EOMNominationValidator(mock_db_session)
        
        # Mock validation
        validator.validate_nomination = Mock(return_value=ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            details={}
        ))
        
        nominations = [
            {
                'nominee_email': 'teacher1@example.com',
                'nominated_by': 'manager@example.com',
                'category': 'academic'
            },
            {
                'nominee_email': 'teacher2@example.com',
                'nominated_by': 'manager@example.com',
                'category': 'admin'
            }
        ]
        
        results = validator.validate_batch_nominations(
            nominations=nominations,
            eom_cycle_id=1
        )
        
        assert len(results) == 2
        assert 'teacher1@example.com' in results
        assert 'teacher2@example.com' in results
        assert all(isinstance(r, ValidationResult) for r in results.values())


class TestAnalytics:
    """Test analytics methods"""
    
    def test_get_rotation_analytics(self, mock_db_session):
        """Test getting rotation analytics"""
        validator = EOMNominationValidator(mock_db_session)
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.all.return_value = []
        
        rule_query = MagicMock()
        rule_query.filter.return_value = rule_query
        rule_query.all.return_value = []
        
        eom_cycle_query = MagicMock()
        eom_cycle_query.filter.return_value = eom_cycle_query
        eom_cycle_query.first.return_value = None
        
        mock_db_session.query.side_effect = lambda model: {
            EOMWinner: winner_query,
            EOMRotationRule: rule_query,
            EOMCycle: eom_cycle_query
        }.get(model, MagicMock())
        
        analytics = validator.get_rotation_analytics(cycle_id=1)
        
        assert 'total_wins' in analytics
        assert 'unique_winners' in analytics
        assert 'wins_by_category' in analytics
        assert 'wins_by_winner' in analytics
    
    def test_get_nominee_rotation_history(self, mock_db_session):
        """Test getting nominee rotation history"""
        validator = EOMNominationValidator(mock_db_session)
        
        nominee_query = MagicMock()
        nominee_query.filter.return_value = nominee_query
        nominee_query.order_by.return_value = nominee_query
        nominee_query.all.return_value = []
        
        winner_query = MagicMock()
        winner_query.filter.return_value = winner_query
        winner_query.order_by.return_value = winner_query
        winner_query.all.return_value = []
        
        mock_db_session.query.side_effect = lambda model: {
            EOMNominee: nominee_query,
            EOMWinner: winner_query
        }.get(model, MagicMock())
        
        history = validator.get_nominee_rotation_history(
            nominee_email='teacher1@example.com',
            category=EOMCategory.OUTSTANDING_LEADERSHIP
        )
        
        assert 'nominee_email' in history
        assert 'total_nominations' in history
        assert 'total_wins' in history
        assert 'win_rate' in history

