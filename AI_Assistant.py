import os
import requests
import openai
from dotenv import load_dotenv
from gtts import gTTS
from IPython.display import Audio
import time
import json
import sqlite3

#Loads environment variables from the .env file
load_dotenv()

#You only need the openai api key if you need to create a new assistant

OpenWeatherAPIkey = os.getenv("OpenWeatherAPIkey")
NewsAPI_key = os.getenv("NewsAPI_key")
PolygonAPI_key = os.getenv("PolygonAPI_key")

name_day_file_id = os.getenv("name_day_file_id")

thread_id = os.getenv("thread_id")
assistant_id = os.getenv("assistant_id")

tools = [
    {
        "type": "function",
        "function": {
            "name": "world_news",
            "description": "Use this function if the user wants to hear the latest news articles.",
            "parameters": {
                "type": "object",
                "properties":{
                    "country": {"type": "string", "description": "The name of a country based on the Alpha-2 codes"}, # e.g., 'us' for the United States
                    "category": {"type": "string", "description": "The category of the query the user wants to search"},   #e.g. 'tech', 'medicine', etc.
                    "q": {"type": "string", "description": "query of the user, for example 'gamestop price'."}   # user's query
                },
                "required": ["country"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_weather",
            "description": "This function returns the weather of a location specified by the user IF the coordinates of the city are specified",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city of witch the user wants to know the weather of"}
                },
                "required": ["city"],
                "strict": "True"
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "random_fact",
            "description": "Call this function if the user wants to hear a RANDOM fact or a fact of the DAY. If the user mentions the word 'day' or 'today' tell him a fact of the day. If the user mentions 'random' tell him a random fact,  Returns a random fact or a fact of the day based on user request",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact_type": {"type": "string", "description": "The type of fact the user want to hear. Either 'day' or 'random'."}
                },
                "required": ["fact_type"],
                "strict" : "True"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "coordinates_city",
            "description": "Returns the longitude and latitude coordinates of a city mentioned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of a city"}
                },
                "required": ["city"],
                "strict" : "True"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stocks_yesterday",
            "description": "Returns the stock value of a mentioned stock(ticker)",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "The 'ticker' value of a stock. For example AAPL for Apple and AMZN for Amazon"}
                },
                "required": ["ticker"],
                "strict" : "True"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "name_days_of_today",
            "description": "Returns the names of people who are celebrating their name day today",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


#ONLY RUN ONCE AND WRITE DOWN THE OUTPUT!!!!
assistant = openai.beta.assistants.update(#.create if you want to create a new assistant or are running the code for the first time
    assistant_id=assistant_id,
    name="MorningAssistant",
    instructions="You are a very talkative morning assistant with access to custom tools that return different responses based on what the user might want to know in the morning.",
    model="gpt-4o-mini",
    tools=tools
)
print(f"Assistant Upadated with ID: {assistant.id}")

#ONLY RUN ONCE AND WRITE DOWN THE OUTPUT!!!! Remember to write down the thread id and replace the thread_id variable value to the printed thread.id value
# thread = openai.beta.threads.create()
# print(f"Thread created with ID: {thread.id}")

def check_for_active_run(thread_id):
    runs = openai.beta.threads.runs.list(thread_id=thread_id)
    for run in runs.data:
        if run.status in ["active", "requires_action"]:
            print(f"Active run found: {run.id} with status {run.status}")
            return True  #If an active run is found, the code will complete it

    return False  #If no active run is found, a new one will be created

#Returns precise coordinates of a city mentioned
def coordinates_city(city, OpenWeatherAPIkey):
    params = {
        "apiKey": OpenWeatherAPIkey, # key for the API connection
        "city": city      # e.g., 'Riga', 'London'
    }
    url = f'https://api.openweathermap.org/geo/1.0/direct?q={city}&limit={2}&appid={OpenWeatherAPIkey}'
    response = requests.get(url)
    if response.status_code==200:
        city = response.json()
        latitude = city[0]['lat']
        longitude = city[0]['lon']
        return latitude, longitude
    else:
        print("API connection Failed!")
        return None, None

#Returns the current weather for set coordinates
def current_weather(latitude, longitude, OpenWeatherAPIkey):
    latitude, longitude = coordinates_city(city, OpenWeatherAPIkey)
    params = {
        "apiKey": OpenWeatherAPIkey, # key for the API connection
        "latitude": latitude,
        "longitude": longitude
    }
    cardinal_directions = ['N', 'N/NE', 'NE', 'E/NE', 'E', 'E/SE', 'SE', 'S/SE', 'S', 'S/SW', 'SW', 'W/SW', 'W', 'W/NW', 'NW', 'N/NW']
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid={OpenWeatherAPIkey}'
    response = requests.get(url)
    if response.status_code==200:
        data = response.json()

        current_weather_pred = data['weather'][0]['description']
        current_temperature = data['main']['temp']
        wind_speed = data ['wind']['speed']
        humidity = data ['main']['humidity']

        wind_direction_deg = data ['wind']['deg']
        ix = round(wind_direction_deg/22.5)
        wind_direction = cardinal_directions[ix]

        print(f'Current temperature is {current_temperature} °C and the weather is {str(current_weather_pred)}. Wind is blowing {wind_direction} with {str(wind_speed)} m/s \n')
        output = f'Current temperature is {str(current_temperature)} °Celciuss and the weather is {str(current_weather_pred)}. Wind is blowing {wind_direction} with {str(wind_speed)} m/s \n\n'
        return output
    else:
        print("API connection Failed!")

#Returns fact of the day OR a random fact bassed on user input

def varda_dienas(name_day_file_id):
    # Connect to the DB. If none exixts, it will be created
    conn = sqlite3.connect("Assitant.db")
    cursor = conn.cursor()

    # A new table is created if none already exists
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS name_days (
            date TEXT,
            name TEXT
            )
    ''')
    cursor.execute("SELECT COUNT(*) FROM name_days")
    row_count = cursor.fetchone()[0]
    if row_count > 0:
            print('Table has entries, skipping creation')
    else:
        print('Table has no entries, creating table')
        url = f'https://drive.google.com/uc?export=download&id={name_day_file_id}'
        response = requests.get(url)
        name_days = response.json()
        if response.status_code==200:
            # Insert each name with its corresponding date
            for date, names in name_days.items():
                for name in names:
                    cursor.execute("INSERT INTO name_days (date, name) VALUES (?, ?)", (date, name))#'?, ?' prevents insertion attacks
        # Commit the changes
        conn.commit()

        # cursor.execute("SELECT * FROM name_days;")
        # rows = cursor.fetchall()
        # for row in rows:
        #     print(f"Date: {row[0]}, Name: {row[1]}")

# Close the connection
    conn.close()

def random_fact(fact_type):
    params = {
        "fact_type": fact_type      # e.g., 'Day' or 'Random'
    }
    print(f'Fact type func: {fact_type}')
    url = f"https://uselessfacts.jsph.pl/api/v2/facts/{fact_type}?language=en"
    response = requests.get(url)
    if response.status_code==200:
        data = response.json()
        output = data['text']
        return output
    else:
        print("API connection Failed!")
        return None

#Returns news which the user wants to know about
def world_news(country, category, query, NewsAPI_key ):
    base_url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NewsAPI_key,
        "country": country,      # e.g., 'us' for the United States
        "category": category,    # e.g., 'technology', 'sports'
        "q": query               # Search query term (e.g., 'elections')
    }
    print("world_news() parameters: ", params)

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        # Check if articles are returned
        if data['articles']:
            # Extract the top news article title and description
            articles = data['articles'][:3]  # Limit to top 3 for brevity
            news_output = ""
            for i, article in enumerate(articles, 1):
                title = article.get("title")
                description = article.get("description")
                news_output += f"{i}. {title}\n{description}\n\n"
            return news_output
        else:
            return "No news articles found for the specified parameters."
    else:
        print("API connection Failed!")
        return None

def stocks_yesterday(ticker, PolygonAPI_key):
    #unix time that needs to be rewinded to previous day in order for the API to work (FREE plan restriction)
    unix_time_1d1h = 88000000
    unix_time_1d = unix_time_1d1h - 3600000

    #Current unix time
    current_time_unix = int(round(time.time() * 1000, 0))
    print('Current unix time: ', current_time_unix )

    #Unix time yesterday and yesterday an hour ago
    unix_from = current_time_unix - unix_time_1d1h
    unix_to = current_time_unix - unix_time_1d

    url = f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/hour/{unix_from}/{unix_to}?adjusted=true&sort=asc&apiKey={PolygonAPI_key}'
    response = requests.get(url)
    print(response.status_code)
    if response.status_code==200:
        data = response.json()
        if data['resultsCount'] == 0:
            output = f"No data found for the specified parameters. Maybe the ticker ({ticker}) is incorrect for the companny you are trying to search"
            return output
        else:
            close_price = data['results'][0]['c']
            output = f'Yesterday\'s closing price for {ticker} was {close_price}'
            return output
    else:
        print("API connection Failed!")
        return None

def name_days_of_today():
    conn = sqlite3.connect("Assitant.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM name_days")
    row_count = cursor.fetchone()[0]
    if row_count > 0:
            print('Table has entries, skipping creation')
    else:
        varda_dienas(name_day_file_id)

    month = time.strftime("%m")#Need to find a way to add dynamic dates, not only today
    date = time.strftime("%d")
    cursor.execute(f"SELECT * FROM name_days WHERE date LIKE '{month}-{date}'")
    rows = cursor.fetchall()
    conn.close()

    names = [row[1] for row in rows]
    output = "The people who celebrate their name day today are: " +  ', '.join(map(str, names))
    return output

#Checks if there is an active run. If there is, a new querry is not generated
if check_for_active_run(thread_id) == True:
    print("Active run found, finishing it!")
else:#Message that the ai assistant will receive
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=input("What would you like to know today?")
)
    #Runs the assistant with message given above
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
)

# Wait for the run to complete
attempt = 1
while run.status != "completed":
    print(f"Run status: {run.status}, attempt: {attempt}")
    run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status == "requires_action":
        break

    if run.status == "failed":
        # Handle the error message if it exists
        if hasattr(run, 'last_error') and run.last_error is not None:
            error_message = run.last_error.message
        else:
            error_message = "No error message found..."

        print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
        print(str(run))

    attempt += 1
    time.sleep(3)

# status "requires_action" means that the assistant decided it needs to call an external tool
# assistant gives us names of tools it needs, we call the corresponding function and return the data back to the assistant
if run.status == "requires_action":
    print("Run requires action, assistant wants to use a tool")
    if run.required_action:
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            print(tool_call)
            tool_params = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {} #Loads the tool_params variable full of key info from the user input (Processed by AI)

            if tool_call.function.name == "current_weather": #Flow for the current_weather() function
                print("current_weather called")
                city = tool_params.get('city')
                latitude, longitude = coordinates_city(city, OpenWeatherAPIkey)
                output = current_weather(latitude, longitude, OpenWeatherAPIkey)

            elif tool_call.function.name == "random_fact": #Flow for the random_fact() function
                fact_type = tool_params.get('fact_type')
                print(f"random_fact called, Fact type: {fact_type}")
                output = random_fact(fact_type)

            elif tool_call.function.name == "coordinates_city": #Flow for the coordinates_city() function
                city = tool_params.get('city')
                print("coordinates_city called")
                output = coordinates_city(city, OpenWeatherAPIkey)

            elif tool_call.function.name == "world_news": #Flow for the world_news() function
                country = tool_params.get('country')
                category = tool_params.get('category')
                q = tool_params.get('q')
                print(f"world_news called, Country: {country}, Category: {category}, Query: {q}")
                output = world_news(country, category, q, NewsAPI_key)

            elif tool_call.function.name == "stocks_yesterday": #Flow for the stocks_yesterday() function
                ticker = tool_params.get('ticker')
                print(f"stocks_yesterday called for {ticker}")
                output = stocks_yesterday(ticker, PolygonAPI_key)

            elif tool_call.function.name == "name_days_of_today": #Flow for the name_days_of_today() function
                print(f"name_days_of_today called")
                output = name_days_of_today()

            else:
                print("Unknown function call")
            print(f"  Generated output: {output}")

            # submit the output back to assistant
            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": str(output)
                }]
            )

if run.status == "requires_action":

    # After submitting tool outputs, we need to wait for the run to complete, again
    run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    attempt = 1
    while run.status not in ["completed", "failed"]:
        print(f"Run status: {run.status}, attempt: {attempt}")
        time.sleep(1)
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        attempt += 1

if run.status == "completed":
    # Retrieve and print the assistant's response
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    final_answer = messages.data[0].content[0].text.value
    print(f"=========\n{final_answer}")
elif run.status == "failed":
    # Handle the error message if it exists
    if hasattr(run, 'last_error') and run.last_error is not None:
        error_message = run.last_error.message
    else:
        error_message = "No error message found..."

    print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
    print(str(run))
else:
    print(f"Unexpected run status: {run.status}")

# response_tts = openai.audio.speech.create(
#     model="tts-1",
#     voice="alloy",
#     input=final_answer,
# )

# response_tts.stream_to_file("output.mp3")

# Converts the final answer from the assistant into TTS which is automatically played after receiving an answer.
text = (final_answer)
tts = gTTS(text)
tts.save("output.mp3")
Audio("output.mp3", autoplay = True)
