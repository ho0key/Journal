from kivy.core.window import Window
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Effect percentages every half hour after a 40mg dose
effect_percent = [0,0,0,50,100,100,100,100,100,100,100,100,100,100,80,60,40,20,0]
time_step = 30
effect_duration = len(effect_percent) * time_step

Window.size = (1200, 600)

DATA_FILE = "doses.json"

class ElvanseSideBySideApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.doses = []
        self.saved_days = {}

        # Load saved data
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.saved_days = json.load(f)
                for day, doses in self.saved_days.items():
                    self.saved_days[day] = [(d[0], datetime.strptime(d[1], "%H:%M")) for d in doses]

        # Initialize current day if empty
        if not self.saved_days:
            self.current_day_index = 1
            self.current_day_name = f"Day {self.current_day_index}"
            self.saved_days[self.current_day_name] = []
        else:
            # Determine next day index
            existing_days = [int(k.split(" ")[1]) for k in self.saved_days.keys()]
            self.current_day_index = max(existing_days) + 1
            self.current_day_name = f"Day {self.current_day_index}"
            self.saved_days[self.current_day_name] = []

        # Root layout
        root_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Scrollable toolbar for days
        self.toolbar_scroll = ScrollView(size_hint=(1, None), height=dp(50), do_scroll_y=False)
        self.toolbar_layout = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_x=None)
        self.toolbar_layout.bind(minimum_width=self.toolbar_layout.setter('width'))
        self.toolbar_scroll.add_widget(self.toolbar_layout)
        root_layout.add_widget(self.toolbar_scroll)

        # Main horizontal layout
        main_layout = BoxLayout(orientation='horizontal', spacing=dp(10))

        # Left panel
        left_panel = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_x=0.35)

        # Input card
        input_card = MDCard(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
        input_card.height = dp(350)

        self.time_input = MDTextField(
            hint_text="Time (HH:MM)",
            helper_text="24h format",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height=dp(50)
        )

        self.dose_input = MDTextField(
            hint_text="Dose (mg)",
            helper_text="Number only",
            helper_text_mode="on_focus",
            input_filter='float',
            size_hint_y=None,
            height=dp(50)
        )

        add_button = MDFlatButton(
            text="Add Dose",
            md_bg_color=(0.1,0.1,0.1,1),
            size_hint_y=None,
            height=dp(50)
        )
        add_button.bind(on_release=self.add_dose)

        save_day_button = MDFlatButton(
            text="Save Day",
            md_bg_color=(0.2,0.2,0.2,1),
            size_hint_y=None,
            height=dp(50)
        )
        save_day_button.bind(on_release=self.save_day)

        self.dose_label = MDLabel(text="No doses added yet.", size_hint_y=None, height=dp(30), halign="center")

        input_card.add_widget(self.time_input)
        input_card.add_widget(self.dose_input)
        input_card.add_widget(add_button)
        input_card.add_widget(save_day_button)
        input_card.add_widget(self.dose_label)
        left_panel.add_widget(input_card)

        # Scrollable dose list
        self.scroll = ScrollView(size_hint=(1,1))
        self.dose_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(5))
        self.dose_list_layout.bind(minimum_height=self.dose_list_layout.setter('height'))
        self.scroll.add_widget(self.dose_list_layout)
        left_panel.add_widget(self.scroll)

        # Right panel: graph
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.65)
        graph_card = MDCard(orientation='vertical', padding=dp(10))
        self.graph_layout = BoxLayout()
        graph_card.add_widget(self.graph_layout)
        right_panel.add_widget(graph_card)

        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)
        root_layout.add_widget(main_layout)

        # Populate toolbar buttons from saved days
        self.refresh_toolbar()

        return root_layout

    def add_dose(self, instance):
        time_str = self.time_input.text.strip()
        dose_str = self.dose_input.text.strip()

        try:
            dose_time = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            self.dose_label.text = "Invalid time. Use HH:MM"
            return

        try:
            dose_amount = float(dose_str)
        except ValueError:
            self.dose_label.text = "Invalid dose. Enter number"
            return

        self.doses.append((dose_amount, dose_time))
        self.dose_label.text = f"Last dose: {dose_amount} mg at {dose_time.strftime('%H:%M')}"

        dose_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        dose_label = MDLabel(text=f"{dose_amount} mg at {dose_time.strftime('%H:%M')}", halign='left')
        delete_button = MDIconButton(icon='close', size_hint_x=None, width=dp(30))

        def delete_dose(btn):
            if (dose_amount, dose_time) in self.doses:
                self.doses.remove((dose_amount, dose_time))
            self.dose_list_layout.remove_widget(dose_row)
            self.update_graph()

        delete_button.bind(on_release=delete_dose)

        dose_row.add_widget(dose_label)
        dose_row.add_widget(delete_button)
        self.dose_list_layout.add_widget(dose_row)

        self.time_input.text = ""
        self.dose_input.text = ""

        self.update_graph()

    def update_graph(self):
        if not self.doses:
            self.graph_layout.clear_widgets()
            return

        reference_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        normalized_doses = [(dose, reference_date.replace(hour=dose_time.hour, minute=dose_time.minute))
                            for dose, dose_time in self.doses]

        start_time = min(dose_time for _, dose_time in normalized_doses)
        end_time = max(dose_time + timedelta(minutes=effect_duration) for _, dose_time in normalized_doses)
        time_range = pd.date_range(start=start_time, end=end_time, freq=f'{time_step}min')
        combined_effect = pd.Series(0, index=time_range)

        for dose, dose_time in normalized_doses:
            dose_scale = dose / 40
            for i, perc in enumerate(effect_percent):
                effect_time = dose_time + timedelta(minutes=i*time_step)
                pos = combined_effect.index.get_indexer([effect_time], method='nearest')[0]
                combined_effect.iloc[pos] += perc * dose_scale

        self.graph_layout.clear_widgets()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(combined_effect.index, combined_effect.values, marker='o', color='cyan')
        ax.set_facecolor('black')
        ax.figure.set_facecolor('black')
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, time_step)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')
        ax.set_xlabel("Time", color='white')
        ax.set_ylabel("Elvanse Effect (%)", color='white')
        ax.set_title("Combined Effect of Elvanse Doses", color='white')
        ax.grid(True, color='gray', linestyle='--', alpha=0.5)
        fig.tight_layout()
        self.graph_layout.add_widget(FigureCanvasKivyAgg(fig))



    def refresh_toolbar(self):
        self.toolbar_layout.clear_widgets()
        for day in sorted(self.saved_days.keys(), key=lambda x: int(x.split(" ")[1])):
            btn = MDFlatButton(text=day, size_hint_x=None, width=dp(120))
            btn.bind(on_release=lambda inst, day_name=day: self.load_day(day_name))
            self.toolbar_layout.add_widget(btn)

    def save_day(self, instance):
        if not self.doses:
            return
        # Save doses as strings
        self.saved_days[self.current_day_name] = [(dose, dt.strftime("%H:%M")) for dose, dt in self.doses]

        # Write to file
        with open(DATA_FILE, "w") as f:
            json.dump(self.saved_days, f)

        # Prepare new blank day
        self.current_day_index += 1
        self.current_day_name = f"Day {self.current_day_index}"
        self.saved_days[self.current_day_name] = []

        self.refresh_toolbar()
        self.doses.clear()
        self.dose_list_layout.clear_widgets()
        self.dose_label.text = "No doses added yet."
        self.update_graph()

    def load_day(self, day_name):
        self.doses.clear()
        self.dose_list_layout.clear_widgets()

        for dose, time_val in self.saved_days[day_name]:
            # Convert to datetime only if string
            if isinstance(time_val, str):
                dose_time = datetime.strptime(time_val, "%H:%M")
            else:
                dose_time = time_val  # already datetime

            self.doses.append((dose, dose_time))

            dose_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
            dose_label = MDLabel(text=f"{dose} mg at {dose_time.strftime('%H:%M')}", halign='left')
            delete_button = MDIconButton(icon='close', size_hint_x=None, width=dp(30))

            def delete_dose(btn, dose=dose, dt=dose_time, row=dose_row):
                if (dose, dt) in self.doses:
                    self.doses.remove((dose, dt))
                self.dose_list_layout.remove_widget(row)
                self.update_graph()

            delete_button.bind(on_release=delete_dose)
            dose_row.add_widget(dose_label)
            dose_row.add_widget(delete_button)
            self.dose_list_layout.add_widget(dose_row)

        self.update_graph()


if __name__ == "__main__":
    ElvanseSideBySideApp().run()
