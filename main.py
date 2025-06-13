import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import random
import os
import time

SUBJECT_FILES = {
    "Bank": "Bank.txt",
    "Audit": "Audit.txt",
    "Budjet": "Budjet.txt",
    "Iqt.Th": "Iqt.Th.txt",
    "Moliya": "Moliya.txt",
    "Pulva": "Pulva.txt",
    "Soliq": "Soliq.txt",
    "Bux": "Bux.txt"
}

class Question:
    def __init__(self, question, options, correct):
        self.question = question
        self.options = options
        self.correct = correct

class MenuScreen(Screen):
    def on_enter(self):
        self.ids.subjects_box.clear_widgets()
        for subject in SUBJECT_FILES:
            btn = Button(text=subject, size_hint_y=None, height=50)
            btn.bind(on_release=lambda btn: self.select_subject(btn.text))
            self.ids.subjects_box.add_widget(btn)
        mix_btn = Button(text="Aralash test (50 ta savol)", size_hint_y=None, height=50)
        mix_btn.bind(on_release=lambda _: self.select_subject("Mixed"))
        self.ids.subjects_box.add_widget(mix_btn)

    def select_subject(self, subject):
        app = App.get_running_app()
        app.load_questions(subject)
        self.manager.current = "quiz"

class QuizScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        app.start_time = time.time()
        self.ids.next_button.disabled = True
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        self.show_question()

    def update_timer(self, dt):
        app = App.get_running_app()
        elapsed = int(time.time() - app.start_time)
        minutes, seconds = divmod(elapsed, 60)
        self.ids.timer_label.text = f"Vaqt: {minutes:02}:{seconds:02}"
        self.ids.progress_label.text = f"Savol {app.current_index+1}/{len(app.questions)} | To‘g‘ri: {app.correct} | Xato: {app.incorrect}"

    def show_question(self):
        app = App.get_running_app()
        self.ids.quiz_box.clear_widgets()
        if app.current_index >= len(app.questions):
            if hasattr(self, 'timer_event'):
                Clock.unschedule(self.timer_event)
            self.manager.current = "results"
            return
        q = app.questions[app.current_index]
        self.ids.question_label.text = q.question
        for opt in q.options:
            btn = Button(
                text=opt,
                size_hint_y=None,
                height=50,
                text_size=(self.width - 40, None),
                halign="left",
                valign="middle"
            )
            btn.bind(on_release=self.check_answer)
            self.ids.quiz_box.add_widget(btn)

    def check_answer(self, instance):
        app = App.get_running_app()
        q = app.questions[app.current_index]
        selected = instance.text.strip()
        correct = q.correct.strip()
        for btn in self.ids.quiz_box.children:
            btn.disabled = True
            if btn.text.strip() == correct:
                btn.background_color = (0, 1, 0, 1)
            elif btn == instance:
                btn.background_color = (1, 0, 0, 1)
        if selected == correct:
            app.correct += 1
        else:
            app.incorrect += 1
            app.incorrect_questions.append(q)
        self.ids.next_button.disabled = False

    def next_question(self):
        app = App.get_running_app()
        app.current_index += 1
        self.ids.next_button.disabled = True
        self.show_question()

class ResultsScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        if not app.questions:
            self.manager.current = "menu"
            return

        elapsed = int(time.time() - app.start_time)
        minutes, seconds = divmod(elapsed, 60)
        result_text = f"To‘g‘ri javoblar: {app.correct}\nXato javoblar: {app.incorrect}\nUmumiy vaqt: {minutes}:{seconds}\n"
        if app.incorrect_questions:
            result_text += "\nXatoliklar:\n"
            for q in app.incorrect_questions:
                result_text += f"\nSavol: {q.question}\nTo‘g‘ri javob: {q.correct}\n"
        self.ids.result_label.text = result_text

    def retry_incorrect(self):
        app = App.get_running_app()
        if not app.incorrect_questions:
            self.manager.current = "menu"
            return
        app.questions = app.incorrect_questions[:]
        app.current_index = 0
        app.correct = 0
        app.incorrect = 0
        app.incorrect_questions = []
        random.shuffle(app.questions)
        self.manager.current = "quiz"

class QuizApp(App):
    def build(self):
        self.title = "UzQuiz"
        Builder.load_file("quiz.kv")
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(QuizScreen(name="quiz"))
        sm.add_widget(ResultsScreen(name="results"))
        return sm

    def load_questions(self, subject):
        all_questions = []
        if subject == "Mixed":
            for file in SUBJECT_FILES.values():
                all_questions.extend(self.parse_questions(file))
            self.questions = random.sample(all_questions, 50)
        else:
            filename = SUBJECT_FILES[subject]
            self.questions = self.parse_questions(filename)
        random.shuffle(self.questions)
        self.current_index = 0
        self.correct = 0
        self.incorrect = 0
        self.incorrect_questions = []

    def parse_questions(self, filename):
        if not os.path.exists(filename):
            print(f"[ERROR] File not found: {filename}")
            return []
        with open(filename, encoding='utf-8') as f:
            lines = f.readlines()
        questions = []
        q, opts, correct = None, [], ""
        for line in lines:
            line = line.strip()
            if line.startswith('?'):
                if q:
                    random.shuffle(opts)
                    questions.append(Question(q, opts, correct))
                q = line[1:].strip()
                opts = []
                correct = ""
            elif line.startswith('+'):
                correct = line[1:].strip()
                opts.append(correct)
            elif line.startswith('-'):
                opts.append(line[1:].strip())
        if q:
            random.shuffle(opts)
            questions.append(Question(q, opts, correct))
        return questions

if __name__ == '__main__':
    QuizApp().run()
