"""Test cases for enhanced authentication features."""

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from allauth.account.forms import SignupForm
from InvenTree.auth_overrides import CustomSignupForm

# [AGENT GENERATED CODE - REQUIREMENT:REQ-AUTH-002, REQ-AUTH-004]
class EnhancedAuthenticationTests(TestCase):
    """Tests for enhanced authentication features."""

    def test_session_timeout_setting(self):
        """Test that session timeout is properly configured."""
        # Should be set to 15 minutes (900 seconds) by default
        self.assertEqual(settings.SESSION_COOKIE_AGE, 60 * 15)
        
        # Session should refresh on every request
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        
    def test_password_validation(self):
        """Test that the password validation rules are properly enforced."""
        form = CustomSignupForm()
        
        # Test password that is too short
        with self.assertRaises(forms.ValidationError) as context:
            form.clean_password1()
            form.cleaned_data = {'password1': 'short'}
            form.clean_password1()
        
        self.assertIn('at least 8 characters', str(context.exception))
        
        # Test password without uppercase
        with self.assertRaises(forms.ValidationError) as context:
            form.cleaned_data = {'password1': 'lowercase123!'}
            form.clean_password1()
        
        self.assertIn('uppercase', str(context.exception))
        
        # Test password without lowercase
        with self.assertRaises(forms.ValidationError) as context:
            form.cleaned_data = {'password1': 'UPPERCASE123!'}
            form.clean_password1()
        
        self.assertIn('lowercase', str(context.exception))
        
        # Test password without numbers
        with self.assertRaises(forms.ValidationError) as context:
            form.cleaned_data = {'password1': 'NoNumbersHere!'}
            form.clean_password1()
        
        self.assertIn('number', str(context.exception))
        
        # Test password without special characters
        with self.assertRaises(forms.ValidationError) as context:
            form.cleaned_data = {'password1': 'NoSpecialChars123'}
            form.clean_password1()
        
        self.assertIn('special character', str(context.exception))
        
        # Test valid password
        form.cleaned_data = {'password1': 'ValidP@ssw0rd'}
        self.assertEqual(form.clean_password1(), 'ValidP@ssw0rd')