from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
from auth_tester import AuthTester

class AuthTestApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Target URL input
        self.layout.add_widget(Label(text='Target URL:'))
        self.url_input = TextInput(text='https://example.com/login', multiline=False)
        self.layout.add_widget(self.url_input)
        
        # Identifiers input
        self.layout.add_widget(Label(text='Identifiers (one per line):'))
        self.identifiers_input = TextInput(text='user1\nuser2\nuser3', height=100)
        self.layout.add_widget(self.identifiers_input)
        
        # Passwords input
        self.layout.add_widget(Label(text='Passwords (one per line):'))
        self.passwords_input = TextInput(text='password123\nadmin123', height=100)
        self.layout.add_widget(self.passwords_input)
        
        # Run button
        self.run_btn = Button(text='Run Test', size_hint_y=None, height=50)
        self.run_btn.bind(on_press=self.run_test)
        self.layout.add_widget(self.run_btn)
        
        # Results area
        self.results_label = Label(text='Results will appear here...', size_hint_y=None, height=200)
        self.layout.add_widget(self.results_label)
        
        return self.layout
    
    def run_test(self, instance):
        self.run_btn.disabled = True
        self.results_label.text = "Running tests...\nPlease wait..."
        
        def test_thread():
            try:
                # Parse inputs
                identifiers = [i.strip() for i in self.identifiers_input.text.split('\n') if i.strip()]
                passwords = [p.strip() for p in self.passwords_input.text.split('\n') if p.strip()]
                
                # Initialize tester
                tester = AuthTester(self.url_input.text, delay=1.0)
                
                # Run tests
                results = tester.run_cross_test(
                    identifiers, passwords, "username",
                    "username", "password"
                )
                
                # Format results
                output = f"Tested: {results['tested_combinations']}\n"
                output += f"Found: {len(results['valid_credentials'])}\n\n"
                if results['valid_credentials']:
                    output += "VALID CREDENTIALS:\n"
                    for cred in results['valid_credentials']:
                        output += f"{cred['identifier']}:{cred['password']}\n"
                
                Clock.schedule_once(lambda dt: self.update_results(output), 0)
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_results(f"Error: {str(e)}"), 0)
            
            Clock.schedule_once(lambda dt: self.enable_button(), 0)
        
        threading.Thread(target=test_thread).start()
    
    def update_results(self, text):
        self.results_label.text = text
    
    def enable_button(self):
        self.run_btn.disabled = False

if __name__ == '__main__':
    AuthTestApp().run()
