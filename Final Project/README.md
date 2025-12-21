# MIXI: Sentiment Analysis & Beverage Mixology

<mark> **Collaborators: Thomas Knoepffler, Carrie Wang, Julia Chen** </mark>

<mark>Our previous project timeline can be found in this [Google Slides Presentation](https://docs.google.com/presentation/d/15_Q3_lkcpeTdOB9RntO9GSOc6RVdMcENesf1MnFc8Mg/edit?usp=sharing) </mark>

---

**\*\*\*1. Background\*\*\***

<mark>This project is a continuation of a previous project conducted in a previous semester within the Design for Physical Interaction I course, a specialized course for M.S. Design Technology students at the Ithaca campus. The original project aimed to develop a telepresent beverage serving machine that facilitated remote communication between individuals. The machine incorporated a concept of emotional analysis, mapping emotions to specific liquids that would be dispensed by the machine. However, the original project primarily served as a speculative proof of concept, lacking the functionality of safely consuming beverages from the device, refilling the beverage container, and the complete integration of AI for taste mapping. The objective of this current iteration is to incorporate these elements while expanding the social aspect of the project, inviting multiple users to utilize the device, rather than limiting it to two participants.</mark>

<mark>Conveniently, CHI 2025 features a recent study on emotion-based mixology, which proposes a similar algorithmic framework linking emotional states to drink compositions. The paper can be found here: [Sip Your Emotions: Blending Emotion and Data in Cocktail Design](https://programs.sigchi.org/chi/2025/program/content/194424)</mark>

<p align="center">
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/MIXI_1.jpg" alt="MIXI 1" width="49.5%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/MIXI_2.jpg" alt="MIXI 2" width="49.5%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/MIXI_3.jpg" alt="MIXI 3" width="49.5%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/MIXI_4.jpg" alt="MIXI 4" width="49.5%"/>
</p>

<mark> _**Image Source:** Original MIXI Project, DESIGN 6397: Physical Interaction I, Fall 2024._ </mark>

**\*\*\*2. User Interaction\*\*\***

<mark>The device was conceptualized to serve an initial user flow, enabling individuals to express their emotions either verbally or through typed text. Upon receiving these inputs, the AI-integrated device would provide personalized recommendations. The device would be designed as a consumer product, accessible to users both in their homes and at various beverage venues. It would adapt to different use cases such as serving a beverage that complements a specific sentiment, or suggest novel recipes that align with the user’s current emotional state.</mark>

![Storyboard](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/Storyboard.png)

<mark> _**AI Usage:** Storyboard generated using Dall-E, ChatGPT. All artifacts preserved._ </mark>

<mark> _**Original Prompt:** "Generate a storyboard for a user that is feeling sad but uses a AI powered beverage device called "MIXI" to make them an ideal drink that changes their mood for the better. Let them also have the option to try out new recipes generated from the AI."_ </mark>

![System Diagram](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/System_Diagram.png)

**\*\*\*3. Electronics Assembly\*\*\***

<mark>The electronics assembly utilized significant integration compared to previous labs, employing both a Raspberry Pi and an Arduino microcontroller. This integration was needed to control six peristaltic pump motors and prevent excessive utilization of the GPIO pins on the Raspberry Pi, which were allocated for the Mini PiTFT screen and rotary encoder. The ultimate electronics assembly comprised of six distinct pump motors connected to a relay, which was interfaced by the Arduino. The Arduino then communicated directly with the Raspberry Pi via serial communication. The Raspberry Pi served as the user interface and control system as well as providing access to the microphone via the webcam and enabling direct Bluetooth connection to a mini speaker.</mark>

**\*\*\*3.1 Components\*\*\***

- <mark> Raspberry Pi 5 Model B/8GB </mark>
- <mark> (6) 5V Peristaltic Pump Motors </mark>
- <mark> 8-Channel 5V Relay </mark>
- <mark> Arduino Micro Pro </mark>
- <mark> Adafruit Mini PiTFT 1.14" 135x240 </mark>
- <mark> Adafruit I2C Stemma QT Rotary Encoder </mark>
- <mark> USB Webcam/Microphone </mark>
- <mark> Mini Bluetooth Speacker </mark>

![Electronics Assembly](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Electronics_Assembly.jpg)
![Componenent Diagram](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/Component_Diagram.png)

<mark> _**AI Usage:** Utilized assistance from ChatGPT and PlanetUML for diagram layout._ </mark>

**\*\*\*4. Fluid Mechanisms\*\*\***

- <mark> Watch Calibration Setup Video: [Calibration Setup](https://drive.google.com/file/d/1KsrHT6vBCfjpTmsm-kpGdOIEWaFsvj8Y/view?usp=sharing) </mark>

- <mark> Watch Mix Testing Video: [Mix Testing](https://drive.google.com/file/d/16aIuF2HokIAy-B7x9K5U18C-VjKTIVIT/view?usp=sharing) </mark>

<mark>One initial challenge we encountered was ensuring the precise calibration of the pump motors to achieve a specific liquid dispensing rate from the container to the cup. Due to the non-standardization of the motors and the physics governing liquid transfer, the length of the tubes also played a crucial role. Consequently, initial calibration and firmware programming into the Arduino were necessary. All tubes were cut to the same length to establish a consistent distance for liquid travel, eliminating it as a variable to consider. We then utilized ChatGPT to generate a calibration code that enabled us to test the motor’s fill-up capacity at least five liquid ounces in a container. We marked the moment when the flow should cease by tracking the time. The period during which the motor operates was used to calculate the exact velocity at which the motor induces the liquid, resulting in the final constants we determined. These constants were then applied across all serialized callbacks to the Arduino, ensuring a consistent amount of liquid is poured into the cup and maintaining the desired ratio of each liquid extracted from its respective container.</mark>

```
// MOTOR CALIBRATION CODE

import time
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD = 9600

PUMP_INDEX = 1          # the pump you calibrated
TARGET_OZ = 5.0         # calibration target

ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
time.sleep(2)

print("Starting calibration...")
print(f"Pump {PUMP_INDEX} ON — press ENTER when cup reaches {TARGET_OZ} fl oz")

start_time = time.time()

# Start pump
ser.write(f"ON {PUMP_INDEX}\n".encode())

input()  # you press enter manually when cup hits 5 oz

# Stop pump
ser.write(f"OFF {PUMP_INDEX}\n".encode())

elapsed = time.time() - start_time

print(f"Elapsed time: {elapsed:.2f} seconds")
```

| Parameter              | Value                          |
| ---------------------- | ------------------------------ |
| Target volume          | 5 fl oz                        |
| Target volume (metric) | 148 mL                         |
| Measured fill time     | 6.77 seconds                   |
| Flow rate              | 21.877 mL / second             |
| Time per mL            | 45.7 ms / mL                   |
| Pump consistency       | All pumps assumed equivalent   |
| Tubing state           | Pre-filled (continuous column) |

**\*\*\*5. Beverage Logic\*\*\***

<mark>Ultimately, we decided to utilize teas as a versatile mixing substrate, enabling the creation of a wide variety of beverages while simultaneously establishing a precise correlation for emotions. Teas have a longstanding history of mapping emotional states and moods, whether it be through calming teas, uplifting teas, energetic teas, cleansing teas, or others. Additionally, teas are increasingly being embraced as a foundational ingredient in mixology. Furthermore, teas are cost-effective and can be brewed in batches, making them efficient for multiple uses and aligning with our objective of batch production, which we had in mind when we initially began testing the device. Below is a table of the tea ingredients we used, the beverage mixture they correspond to, and the amount of parts one would need to in order to brew that particular batch.</mark>

| Emotion    | Beverage Name    | Black Tea | Green Tea | Rooibos Tea | Chamomile Tea | Lemon Tea | Sparkling Water |
| ---------- | ---------------- | --------- | --------- | ----------- | ------------- | --------- | --------------- |
| Happiness  | Golden Glow      | 10        | 10        | 0           | 20            | 40        | 70              |
| Sadness    | Warm Quiet Tea   | 0         | 10        | 25          | 45            | 10        | 60              |
| Stress     | Stillness Cooler | 5         | 40        | 10          | 15            | 5         | 75              |
| Excitement | Citrus Spark     | 30        | 0         | 15          | 0             | 40        | 65              |
| Calm       | Soft Meadow      | 0         | 25        | 15          | 45            | 10        | 55              |
| Surprise   | Crimson Twist    | 10        | 5         | 40          | 10            | 25        | 60              |

![Menu 1](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Graphics/Menu_1.png)
![Menu 2](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Graphics/Menu_2.png)

**\*\*\*6. Coding Stack\*\*\***

<mark> Our code can be found at [mixi.py](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/mixi.py), [matrix.yaml](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/matrix.yaml), and [firmware.ino](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/firmware.ino) </mark>

<mark> _**AI Usage:** Utilized assistance from Cursor for the writing of code._ </mark>

<mark> _**Pros:** Cursor has proven to be overall much more efficient than other LLMs since it analyzes the entirety of the code based into its context and is able to make quick changes without having to backtrack or manually search for the instances of code that need to be changed._ </mark>

<mark> _**Cons:** Since the changes are carried out with it every single prompt command, certain changes that would like to not be preserved versus those that would are hard to discern. The element of version control is an added benefit, but ultimately there needs to be more finer user control over what code elements are changed, and which remain the same._ </mark>

<mark>The primary configuration is loaded from the .yaml (Pi) file and establishes a fixed ordering of ingredients, a closed set of emotion labels, and recipe definitions expressed as proportional arrays. The .py (Pi) file maintains a state loop that handles menu navigation, mode switching, and user actions. It also calls the OpenAI API to engage in text classification for sentiment analysis. When an emotion is selected—either manually or via text classification via ChatGPT—the corresponding recipe array is retrieved, normalized to a fixed total volume by proportional scaling, and serialized to the .ino (Arduino) file to handle the pump logics.</mark>

**\*\*\*6.1 Dependencies\*\*\***

- <mark> Arduino.h </mark>
- <mark> pyserial </mark>
- <mark> pyyaml </mark>
- <mark> numpy </mark>
- <mark> sounddevice </mark>
- <mark> SpeechRecognition </mark>
- <mark> pillow </mark>
- <mark> openai </mark>

![UML Diagram](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/UML_Diagram.png)

<mark> _**AI Usage:** Utilized assistance from ChatGPT and PlanetUML for diagram layout._ </mark>

**\*\*\*7. Form Factor\*\*\***

<mark>The exploration of form factors encompassed various image references to arrayed beverage machines or siphon valves, drawing inspiration from tonics, tinctures, and other scent-related confluences. The primary source for the majority of these images was Pinterest.</mark>

<p align="center">
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Inspiration_1.jpg" alt="Inspiration 1" width="49.5%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Inspiration_2.jpg" alt="Inspiration 2" width="49.5%"/>
</p>

<mark> \_**Image Source:** Images found from Pinterest for keywords: "Beverage Bar," "Siphon Array," "Glass Arrangements," etc. </mark>

**\*\*\*8. Technical Drawings\*\*\***

<mark>3D models were created using Rhino and Grasshopper. The primary fabrication method was laser cutting, so models were flattened and transcribed in Adobe Illustrator for the cutting of each face of the device, keeping in mind thickness of materials. These individual faces were subsequently assembled manually using wood adhesives and finished with sandpaper.</mark>

**\*\*\*8.1 Materials\*\*\***

- <mark> 1/16" Balsawood Stock </mark>
- <mark> 1/4" ID x 3/8" OD Clear Tubing </mark>
- <mark> Fine Grain Sandpaper </mark>
- <mark> Black Felt </mark>
- <mark> Wood Glue </mark>

![Technical Sections](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/Technical_Sections.png)
![Technical Isometric](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Diagrams/Technical_Isometric.png)

**\*\*\*9. Full Assembly\*\*\***

![Assembly 1](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_1.jpg)
![Assembly 2](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_2.jpg)
![Assembly 3](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_3.jpg)
![Assembly 4](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_4.jpg)
![Assembly 5](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_5.jpg)
![Assembly 6](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_6.jpg)
![Assembly 7](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_7.jpg)
![Assembly 8](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_8.jpg)
![Assembly 9](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_9.jpg)
![Assembly 10](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Assembly_10.jpg)

**\*\*\*10. User Testing\*\*\***

- <mark> Watch User Testing Video # 1: [User Testing #1: Part 1](https://drive.google.com/file/d/1ng0rriCnv4IIJMrV4pIEbAiaqybnliK9/view?usp=sharing) and [User Testing #1: Part 2](https://drive.google.com/file/d/1h4tnX7UXlHBnixwkRbmMY9bSQM1rhkLw/view?usp=sharing)</mark>

- <mark> Watch User Testing Video # 2: [User Testing #2: Part 1](https://drive.google.com/file/d/1AeCpl_paqU5a5wBIbb9jwm_wgQ3LofRY/view?usp=sharing) and [User Testing #2: Part 2](https://drive.google.com/file/d/1_AxzxZydFRWsPnGCHymTg6LKP1zpls3W/view?usp=sharing)</mark>

<mark>During the showcase, we conducted user testing with a vast range of participants. The majority were from the interactive device design class, while a few participants, particularly those providing detailed feedback, worked in the maker space or adjacent to the Cornell Tech ecosystem. Five batches of iced tea were brewed the previous evening and chilled overnight to create five reservoirs of ice tea, each with an added sparkling water element. Users were given the option to either select a drink from the printed menu or engage with the AI bartender for a recommendation. All interaction elements were prominently displayed and illuminated with a lamp to ensure user awareness of the available options. Team members were also present to assist participants throughout the process.</mark>

![Demo 1](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/GIFs/Demo_1.gif)
![Demo 2](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/GIFs/Demo_2.gif)

![Showcase 1](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Showcase_1.jpg)
![Showcase 2](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Showcase_2.jpg)
![Showcase 3](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Showcase_3.jpg)

**\*\*\*11. Reflections\*\*\***

<mark>The interactive device gained significant popularity and was engaged with multiple times throughout the night. Participants were eager to utilize the device, possibly motivated by the prospect of obtaining a personalized beverage at the conclusion of the interaction. The project also received positive feedback regarding its form factor, with appreciation expressed for the wood materials used and the overall compactness of the system. However, some critiques proved to be valuable for future iterations on the project.</mark>

<mark>One critique suggested implementing a more sophisticated AI taste pipeline. The current setup involves fixing labels to sentiment. One participant expressed interest in creating a system that maps each individual word in the dialogue and transforms it into the subsequent recipe, resulting in a more nuanced and potentially more complex beverage with various competing sentiment vectors influencing the overall taste. Additionally, participants noted that the machine was somewhat messy, dripping excess tea even before the pumps began. They also had to remain dry to prevent warping or bending the wood. This issue could be mitigated by using a siphon that allows all the tubes to converge at a single point, enabling the spigot to dispense the mixed beverages in one centralized location.</mark>

<mark>Another problem was that most participants remained within the more positively affiliated affects and sentiments, such as happiness or excitement. As a means of encouraging individuals to explore other sentiments or even more complex emotions, changes in the flow or invitation to interaction would need to be considered to ensure that users can engage in the majority of the system’s features rather than remaining limited to a shallow end of the emotional spectrum.</mark>

**\*\*\*12. Conclusions\*\*\***

<mark>Toward the end of the showcase, a clear pattern emerged: participants expressed a desire for more direct, self-directed engagement with the system. While initial interactions were mediated by team members—who navigated menus and physically handled the device—participants increasingly sought to operate the system themselves. In response, facilitation was reduced, allowing users to engage independently except where intervention was necessary. This shift highlights a central principle of the course: the importance of intentional physical interaction in design practice. Effective interaction design should support experiences that are not only legible and functional, but also empowering, enabling users to engage with systems in ways that feel comfortable, intuitive, and aligned with their sense of agency. This observation reinforces the value of designing interactions that ultimately recede, allowing users to act freely within them.</mark>

<mark> Collaborators: Thomas Knoepffler (Digital Fabrication & Assembly), Carrie Wang (3D Modeling & User Experience), Julia Chen (Hardware & Software Engineer) </mark>

<p align="center">
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Bonus_1.jpg" alt="Bonus 1" width="33%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Bonus_2.jpg" alt="Bonus 2" width="33%"/>
<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/Images/Bonus_3.jpg" alt="Bonus 3" width="33%"/>
</p>
