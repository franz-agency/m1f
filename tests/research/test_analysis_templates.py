"""
Tests for analysis templates
"""
import pytest
from tools.research.analysis_templates import (
    get_template,
    TEMPLATES,
    TECHNICAL_TEMPLATE,
    ACADEMIC_TEMPLATE,
    TUTORIAL_TEMPLATE,
    REFERENCE_TEMPLATE,
    GENERAL_TEMPLATE,
    apply_template_scoring
)


class TestAnalysisTemplates:
    """Test analysis template functionality"""
    
    def test_all_templates_exist(self):
        """Test that all templates are registered"""
        expected_templates = ['general', 'technical', 'academic', 'tutorial', 'reference']
        assert set(TEMPLATES.keys()) == set(expected_templates)
    
    def test_get_template(self):
        """Test template retrieval"""
        assert get_template('technical') == TECHNICAL_TEMPLATE
        assert get_template('academic') == ACADEMIC_TEMPLATE
        assert get_template('tutorial') == TUTORIAL_TEMPLATE
        assert get_template('reference') == REFERENCE_TEMPLATE
        assert get_template('general') == GENERAL_TEMPLATE
        
        # Test fallback for unknown template
        assert get_template('unknown') == GENERAL_TEMPLATE
    
    def test_template_structure(self):
        """Test that all templates have required fields"""
        required_fields = [
            'name', 'description', 'focus_areas', 
            'evaluation_criteria', 'prompts', 'content_preferences'
        ]
        
        for template_name, template in TEMPLATES.items():
            for field in required_fields:
                assert hasattr(template, field), f"{template_name} missing {field}"
            
            # Check prompts has required keys
            assert 'relevance' in template.prompts
            assert 'key_points' in template.prompts
    
    # def test_customize_analysis_prompt(self):
    #     """Test prompt customization"""
    #     template = TECHNICAL_TEMPLATE
    #     query = "python async programming"
    #     
    #     # Test relevance prompt
    #     relevance_prompt = customize_analysis_prompt(template, 'relevance', query)
    #     assert query in relevance_prompt
    #     assert "implementation details" in relevance_prompt.lower()
    #     
    #     # Test key points prompt
    #     key_points_prompt = customize_analysis_prompt(template, 'key_points', query)
    #     assert "implementation patterns" in key_points_prompt.lower()
    
    def test_template_scoring(self):
        """Test template-based scoring"""
        # Test with technical template
        tech_analysis = {
            'relevance_score': 8.0,
            'summary': 'A detailed technical implementation guide',
            'key_points': ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5'],
            'content_type': 'tutorial',
            'technical_level': 'advanced'
        }
        
        tech_score = apply_template_scoring(TECHNICAL_TEMPLATE, tech_analysis)
        assert 0 <= tech_score <= 10
        
        # Test with academic template
        academic_analysis = {
            'relevance_score': 7.0,
            'summary': 'A theoretical analysis of the concept',
            'key_points': ['Theory 1', 'Theory 2', 'Theory 3'],
            'content_type': 'research',
            'technical_level': 'intermediate'
        }
        
        academic_score = apply_template_scoring(ACADEMIC_TEMPLATE, academic_analysis)
        assert 0 <= academic_score <= 10
    
    def test_template_content_preferences(self):
        """Test that templates have appropriate content preferences"""
        # Technical template should prefer code
        assert TECHNICAL_TEMPLATE.content_preferences['prefer_code_examples'] is True
        assert TECHNICAL_TEMPLATE.content_preferences['min_code_ratio'] > 0
        
        # Academic template should not prefer code
        assert ACADEMIC_TEMPLATE.content_preferences['prefer_code_examples'] is False
        assert 'min_citation_count' in ACADEMIC_TEMPLATE.content_preferences
        
        # Tutorial template should prefer numbered steps
        assert TUTORIAL_TEMPLATE.content_preferences['prefer_numbered_steps'] is True
        
        # General template should be balanced
        assert GENERAL_TEMPLATE.content_preferences['balanced_content'] is True
    
    def test_evaluation_criteria_weights(self):
        """Test that evaluation criteria weights sum to reasonable values"""
        for template_name, template in TEMPLATES.items():
            total_weight = sum(template.evaluation_criteria.values())
            # Weights should sum to approximately 1.0
            assert 0.9 <= total_weight <= 1.1, f"{template_name} weights sum to {total_weight}"