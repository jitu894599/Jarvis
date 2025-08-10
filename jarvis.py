import pyttsx3
import speech_recognition as sr
import datetime
import webbrowser
import os
import time
import socket
from email.message import EmailMessage
import screen_brightness_control as sbc
import threading
from PIL import Image

engine = pyttsx3.init()
engine.setProperty('rate', 170)
voices = engine.getProperty('voices')
male_voice = None
for voice in voices:
    if "male" in voice.name.lower():
        male_voice = voice.id
        break
engine.setProperty('voice', male_voice if male_voice else voices[0].id)

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def check_connection():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def wish_user():
    hour = datetime.datetime.now().hour
    if 1 <= hour < 12:
        speak("Good morning Jeet!")  # your name here
    elif 12 <= hour < 17:
        speak("Good afternoon Jeet!")
    elif 17 <= hour < 24:
        speak("Good evening Jeet!")
    else:
        speak("Hello!")
    speak("I am Jarvis. Your Personal Assistant. How can I help you?")

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        r.energy_threshold = 200
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Timeout. No speech detected.")
            return ""

    try:
        query = r.recognize_google(audio, language='en-in')
        print(f"Recognized: {query}")
        return query.lower()
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print("API error:", e)
        return ""

def get_input(prompt):
    speak(prompt)
    response = take_command()
    if not response:
        response = input(f"{prompt} (Type here): ")
    return response

def speech_only_input(prompt):
    speak(prompt)
    for _ in range(2):
        response = take_command()
        if response:
            return response
        speak("I didn't catch that. Please say it again.")
    return "No input"

def take_picture():
    import cv2
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        filename = f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        speak(f"Picture taken and saved as {filename}")
    else:
        speak("Failed to access the camera.")
    cam.release()
    cv2.destroyAllWindows()

def set_alarm(time_str):
    def alarm():
        now = datetime.datetime.now()
        alarm_time = datetime.datetime.strptime(time_str, "%H:%M")
        alarm_time = alarm_time.replace(year=now.year, month=now.month, day=now.day)
        if alarm_time < now:
            alarm_time += datetime.timedelta(days=1)
        wait_time = (alarm_time - now).total_seconds()
        time.sleep(wait_time)
        speak("Wake up! This is your alarm.")

    threading.Thread(target=alarm).start()

def set_reminder(time_str, message):
    def reminder():
        now = datetime.datetime.now()
        remind_time = datetime.datetime.strptime(time_str, "%H:%M")
        remind_time = remind_time.replace(year=now.year, month=now.month, day=now.day)
        if remind_time < now:
            remind_time += datetime.timedelta(days=1)
        wait_time = (remind_time - now).total_seconds()
        time.sleep(wait_time)
        speak(f"Reminder: {message}")

    threading.Thread(target=reminder).start()

def search_wikipedia():
    import wikipedia
    speak("What should I search on Wikipedia?")
    query = take_command()

    if not query:
        speak("I didn't catch that. Please try again.")
        return

    query = query.strip()

    try:
        speak("Searching Wikipedia...")
        summary = wikipedia.summary(query, sentences=2)

        speak(f"According to Wikipedia: {summary}")

        speak(f"Do you want to know more about {query}? Say yes or no.")
        time.sleep(1)

        follow_up = ""
        retry_count = 0

        while retry_count < 3 and follow_up.strip() == "":
            follow_up = take_command().lower().strip()
            print(f"User said (raw): {follow_up}") 
            retry_count += 1

        if follow_up.strip() == "":
            speak("I didn't catch that. You can type your answer.")
            follow_up = input("Your answer: ").lower().strip()

        yes_words = {"yes", "yeah", "sure", "yup", "ok", "okay"}
        no_words = {"no", "nope", "nah"}

        follow_words = follow_up.split()

        if any(word in yes_words for word in follow_words):
            url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            webbrowser.open(url)
            speak("Opening the full Wikipedia article.")
        elif any(word in no_words for word in follow_words):
            speak("Okay, moving on.")
        else:
            speak("I still didn't understand. Skipping this topic.")

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        speak("Your search term is too broad. Did you mean:")
        for i, option in enumerate(options, start=1):
            speak(f"{i}. {option}")

        speak("Please say the number of your choice.")
        choice = take_command().strip()

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(options):
                selected = options[index]
                try:
                    result = wikipedia.summary(selected, sentences=2)
                    speak(f"According to Wikipedia: {result}")
                    speak(f"Do you want to know more about {selected}? Say yes or no.")
                    
                    follow_up = ""
                    retry_count = 0
                    while retry_count < 2 and follow_up.strip() == "":
                        follow_up = take_command().lower().strip()
                        retry_count += 1

                    if "yes" in follow_up:
                        url = f"https://en.wikipedia.org/wiki/{selected.replace(' ', '_')}"
                        webbrowser.open(url)
                        speak("Opening the full article.")
                    elif "no" in follow_up:
                        speak("Okay, moving on.")
                    else:
                        speak("I didn't understand. Skipping this topic.")
                except Exception as ex:
                    print("Wikipedia summary fetch error:", ex)
                    speak("Sorry, I couldn't fetch that topic.")
            else:
                speak("Invalid number.")
        else:
            speak("Invalid response. Skipping this topic.")

    except wikipedia.exceptions.PageError:
        speak("No page found on Wikipedia for that topic.")

    except Exception as e:
        print("Wikipedia Error:", str(e))
        speak("There was a problem searching Wikipedia.")


def get_weather(city):
    import requests

    api_key ="Weather api key here"
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    response = requests.get(base_url, params=params)
    data = response.json()

    if data["cod"] == 200:
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        speak(f"The weather in {city} is {weather} with a temperature of {temp} degree Celsius.")
    else:
        speak("Sorry, I couldn't fetch the weather.")

def get_news(city):
    import requests

    api_key = "news api key here"
    url = f"https://newsapi.org/v2/everything?q={city}&apiKey={api_key}&pageSize=5"
    
    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] == "ok":
            articles = data["articles"]
            if articles:
                speak(f"Here are the top headlines for {city}:")
                for article in articles[:5]:
                    speak(article["title"])
            else:
                speak(f"No recent news found for {city}.")
        else:
            speak("Failed to fetch news.")
    except Exception as e:
        speak(f"An error occurred while fetching the news: {str(e)}")

def open_google_maps(command):
    if "locate" in command:
        location = command.replace("locate", "").strip()
        speak(f"Locating {location} on Google Maps...")
        webbrowser.open(f"https://www.google.com/maps/place/{location}")

    elif "directions from" in command and "to" in command:
        parts = command.split("to")
        source = parts[0].replace("directions from", "").strip()
        destination = parts[1].strip()
        speak(f"Getting directions from {source} to {destination}")
        webbrowser.open(f"https://www.google.com/maps/dir/{source}/{destination}")

    elif "near me" in command:
        place_type = command.replace("find", "").replace("near me", "").strip()
        speak(f"Searching for {place_type} near your location...")
        webbrowser.open(f"https://www.google.com/maps/search/{place_type}+near+me")
    else:
        speak("Sorry, I couldn't understand the location command.")

def take_screenshot():
    import pyautogui

    filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    image = pyautogui.screenshot()
    image.save(filename)
    speak(f"Screenshot saved as {filename}")

def record_video(duration=10):
    import cv2
    speak(f"Recording video for {duration} seconds.")
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    filename = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
    start_time = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            cv2.imshow('Recording (press Q to stop)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or time.time() - start_time > duration:
                break
        else:
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    speak(f"Video recorded and saved as {filename}")

def system_info():
    import platform
    import socket

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    os_info = f"{platform.system()} {platform.release()}"
    speak(f"Computer name: {hostname}")
    speak(f"IP address: {ip_address}")
    speak(f"Operating system: {os_info}")

def set_volume(level):
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level / 100, None)
    speak(f"Volume set to {level} percent")

def increase_volume(step=10):
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = min(current + step / 100, 1.0)
    volume.SetMasterVolumeLevelScalar(new_volume, None)
    speak("Volume increased")

def decrease_volume(step=10):
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = max(current - step / 100, 0.0)
    volume.SetMasterVolumeLevelScalar(new_volume, None)
    speak("Volume decreased")

def set_brightness(level):
    import screen_brightness_control as sbc

    try:
        sbc.set_brightness(level)
        speak(f"Brightness set to {level} percent")
    except Exception as e:
        speak("Failed to set brightness")

def battery_status():
    import psutil
    speak("Checking battery status...")

    battery = psutil.sensors_battery()
    percent = battery.percent
    plugged = battery.power_plugged
    status = "charging" if plugged else "not charging"
    speak(f"Battery is at {percent} percent and it is currently {status}")

def system_health():
    import psutil

    speak("Checking system health...")
    speak("Gathering CPU and memory usage statistics.")

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    speak(f"CPU usage is at {cpu} percent and memory usage is at {memory} percent.")


def send_email(sender, password, recipient, subject, message):
    import smtplib

    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

        speak("Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        speak("Authentication failed. Please check your email or app password.")
    except Exception as e:
        speak(f"Failed to send email. {str(e)}")

def shutdown_system():
    speak("Shutting down the system.")
    os.system("shutdown /s /t 5")  # Shutdown in 5 seconds

def restart_system():
    speak("Restarting the system.")
    os.system("shutdown /r /t 5")  # Restart in 5 seconds

def confirm_and_shutdown():
    speak("Are you sure you want to shut down?")
    response = take_command().lower()
    if "yes" in response:
        shutdown_system()
    else:
        speak("Shutdown cancelled.")

def confirm_and_restart():
    speak("Are you sure you want to restart?")
    response = take_command().lower()
    if "yes" in response:
        restart_system()
    else:
        speak("Restart cancelled.")

def run_jarvis():
    if not check_connection():
        speak("Internet is not available. Please connect to proceed.")
        return

    wish_user()

    while True:
        command = take_command()
        if not command:
            continue

        if "wikipedia" in command:
            search_wikipedia()

        elif "hello jarvis" in command:
            speak("Hello sir, how can I help you?")

        elif "open youtube" in command:
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")

        elif "open google" in command:
            speak("Opening Google")
            webbrowser.open("https://www.google.com")
            time.sleep(2)
            search_query = speech_only_input("What do you want to search on Google?")
            if search_query.lower() != "no input":
                speak(f"Searching for {search_query} on Google")
                webbrowser.open(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")

        elif "play" in command and "youtube" in command:
            import pywhatkit

            speak("What song should I play on YouTube?")
            song = command.replace("play", "").replace("on youtube", "").replace("in youtube", "").strip()
            if not song:
                song = get_input("What song should I play?")
            speak(f"Playing {song} on YouTube")
            pywhatkit.playonyt(song)

        elif "what is the time" in command:
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {now}")

        elif "take a picture" in command or "take photo" in command:
            take_picture()

        elif "screenshot" in command or "take screenshot" in command:
            take_screenshot()

        elif "record video" in command or "start video recording" in command:
            duration = get_input("For how many seconds?")
            try:
                record_video(int(duration))
            except:
                speak("Invalid duration. Using 10 seconds default.")
                record_video(10)

        elif "system info" in command or "system information" in command:
            system_info()

        elif "set volume to" in command:
            try:
                level = int(''.join(filter(str.isdigit, command)))
                set_volume(level)
            except:
                speak("Please say a valid volume level like 'set volume to 50'")

        elif "increase volume" in command:
            increase_volume()

        elif "decrease volume" in command:
            decrease_volume()

        elif "set brightness to" in command:
            try:
                level = int(''.join(filter(str.isdigit, command)))
                set_brightness(level)
            except:
                speak("Please say a valid brightness level like 'set brightness to 70'")

        elif "battery status" in command or "battery level" in command:
            battery_status()

        elif "system health" in command or "check performance" in command:
            system_health()

        elif "set alarm" in command:
            speak("Please tell me the time for the alarm in 24-hour format like 07:30")
            time_str = take_command()
            set_alarm(time_str)
            speak(f"Alarm set for {time_str}")

        elif "set reminder" in command:
            speak("Please tell me the time for the reminder in 24-hour format like 15:30")
            time_str = take_command()
            speak("What should I remind you about?")
            message = take_command()
            set_reminder(time_str, message)
            speak(f"Reminder set for {time_str} with message: {message}")


        elif "lock the system" in command:
            speak("Locking the system now.")
            os.system("rundll32.exe user32.dll,LockWorkStation")

        elif "send email" in command:
            default_sender = "example@gmail.com"
            speak(f"Your email address is {default_sender}. Is that correct? Say yes or no.")
            print(f"Default email: {default_sender}")
            confirmation = take_command()

            if "no" in confirmation:
                sender = get_input("What is your correct email address?")
            else:
                sender = default_sender

            speak("Please type your password for security.")
            print("Please type your password for security.")
            password = input("Enter your email password (App Password if using Gmail): ")

            speak("Who is the recipient?")
            recipient = input("Enter the recipient's email address: ")
            print(f"Recipient Email: {recipient}")
            speak(f"The recipient email address is {recipient}")

            subject = speech_only_input("What is the subject of the email?")
            message = speech_only_input("What is the message to send?")
            send_email(sender, password, recipient, subject, message)

        elif "open vs code" in command:
            speak("Opening VS Code.")
            os.system("code")  # Only works if 'code' is added to PATH

        elif "open chrome" in command:
            speak("Opening Chrome.")
            os.system("start chrome")

        elif "open whatsapp" in command:
            speak("Opening WhatsApp.")
            os.system("start whatsapp:") 

        elif "send whatsapp" in command or "send whatsapp message" in command:
            import pywhatkit

            speak("Tell me the phone number of the person you want to message, starting with the country code.")
            number = take_command().replace(" ", "").replace("+", "")
            if not number:
                number = input("Enter phone number (with country code, e.g. 919876543210): ")

            if not number.startswith("91") and not number.startswith("+"):
                number = "+91" + number
            elif not number.startswith("+"):
                number = "+" + number

            speak("What is the message?")
            message = speech_only_input("Please speak your message.")

            if message.lower() != "no input":
                try:
                    speak(f"Sending your WhatsApp message to {number}")
                    pywhatkit.sendwhatmsg_instantly(number, message, wait_time=10, tab_close=True)
                    speak("Message sent successfully.")
                except Exception as e:
                    speak(f"Failed to send WhatsApp message. Error: {str(e)}")
            else:
                speak("Message not sent due to empty input.")

        elif "weather" in command or "weather report" in command or "weather like" in command:
            city = get_input("Which city do you want the weather for?")
            if city:
                get_weather(city)
            else:
                speak("I didn't get the city name. Please try again.")

        elif any(word in command for word in ["news", "headlines", "news headlines"]):
            city = get_input("Which city's news do you want?")
            if city:
                get_news(city)
            else:
                speak("I didn't get the city name. Please try again.")

        elif "map" in command or "locate" in command or "direction" in command or "near me" in command or "open map" in command:
            if "open map" in command:
                speak("Opening Google Maps.")
                webbrowser.open("https://www.google.com/maps")
            else:
                open_google_maps(command)

        elif "your creator" in command:
            speak("I was created by Mr. Jeet Dey.")

        elif "shutdown" in command:
            confirm_and_shutdown()

        elif "restart" in command:
            confirm_and_restart()

        elif "exit" in command or "stop" in command:
            speak("Goodbye! Have a great day.")
            break

        else:
            speak("I didn't understand that. Could you please repeat?")

if __name__ == "__main__":
    try:
        run_jarvis()
    except KeyboardInterrupt:
        speak("Jarvis shutting down. Goodbye!")

