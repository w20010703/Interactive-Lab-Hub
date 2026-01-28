# Final Project: MIXI

**Collaborators:** Thomas Knoepffler (Digital Fabrication & Assembly), Carrie Wang (3D Modeling & User Experience), Julia Chen (Hardware & Software Engineer)

Our previous project timeline can be found in this [Google Slides Presentation](https://docs.google.com/presentation/d/15_Q3_lkcpeTdOB9RntO9GSOc6RVdMcENesf1MnFc8Mg/edit?usp=sharing)

## Background

This project is a continuation of a previous project conducted in a previous semester within the Design for Physical Interaction I course, a specialized course for M.S. Design Technology students at the Ithaca campus. The original project aimed to develop a telepresent beverage serving machine that facilitated remote communication between individuals. The machine incorporated a concept of emotional analysis, mapping emotions to specific liquids that would be dispensed by the machine. However, the original project primarily served as a speculative proof of concept, lacking the functionality of safely consuming beverages from the device, refilling the beverage container, and the complete integration of AI for taste mapping. The objective of this current iteration is to incorporate these elements while expanding the social aspect of the project, inviting multiple users to utilize the device, rather than limiting it to two participants.

Conveniently, CHI 2025 features a recent study on emotion-based mixology, which proposes a similar algorithmic framework linking emotional states to drink compositions. The paper can be found here: [Sip Your Emotions: Blending Emotion and Data in Cocktail Design](https://programs.sigchi.org/chi/2025/program/content/194424)

![MIXI](assets/mixi.png)

_Image Source:_ Original MIXI Project, DESIGN 6397: Physical Interaction I, Fall 2024.

## User Interaction

The device was conceptualized to serve an initial user flow, enabling individuals to express their emotions either verbally or through typed text. Upon receiving these inputs, the AI-integrated device would provide personalized recommendations. The device would be designed as a consumer product, accessible to users both in their homes and at various beverage venues. It would adapt to different use cases such as serving a beverage that complements a specific sentiment, or suggest novel recipes that align with the user’s current emotional state.

![Storyboard](assets/storyboard.png)

_AI Usage:_ Storyboard generated using Dall-E, ChatGPT. All artifacts preserved.

_Original Prompt:_ "Generate a storyboard for a user that is feeling sad but uses a AI powered beverage device called "MIXI" to make them an ideal drink that changes their mood for the better. Let them also have the option to try out new recipes generated from the AI."

![Diagram](assets/diagram.png)

## Electronics Assembly

The electronics assembly utilized significant integration compared to previous labs, employing both a Raspberry Pi and an Arduino microcontroller. This integration was needed to control six peristaltic pump motors and prevent excessive utilization of the GPIO pins on the Raspberry Pi, which were allocated for the Mini PiTFT screen and rotary encoder. The ultimate electronics assembly comprised of six distinct pump motors connected to a relay, which was interfaced by the Arduino. The Arduino then communicated directly with the Raspberry Pi via serial communication. The Raspberry Pi served as the user interface and control system as well as providing access to the microphone via the webcam and enabling direct Bluetooth connection to a mini speaker.

### Components

- Raspberry Pi 5 Model B/8GB
- (6) 5V Peristaltic Pump Motors
- 8-Channel 5V Relay
- Arduino Micro Pro
- Adafruit Mini PiTFT 1.14" 135x240
- Adafruit I2C Stemma QT Rotary Encoder
- USB Webcam/Microphone
- Mini Bluetooth Speaker

![Electronics](assets/electronics.png)
![System](assets/system.png)

_AI Usage:_ Utilized assistance from ChatGPT and PlantUML for diagram layout.

## Fluid Mechanisms

[![Calibration Setup Thumbnail](assets/calibration_thumb.png)](https://youtu.be/LPgmXyhD6Zw)  
[Watch Calibration Setup on YouTube](https://youtu.be/LPgmXyhD6Zw)

One initial challenge we encountered was ensuring the precise calibration of the pump motors to achieve a specific liquid dispensing rate from the container to the cup. Due to the non-standardization of the motors and the physics governing liquid transfer, the length of the tubes also played a crucial role. Consequently, initial calibration and firmware programming into the Arduino were necessary. All tubes were cut to the same length to establish a consistent distance for liquid travel, eliminating it as a variable to consider. We then utilized ChatGPT to generate a calibration code that enabled us to test the motor’s fill-up capacity at least five liquid ounces in a container. We marked the moment when the flow should cease by tracking the time. The period during which the motor operates was used to calculate the exact velocity at which the motor induces the liquid, resulting in the final constants we determined. These constants were then applied across all serialized callbacks to the Arduino, ensuring a consistent amount of liquid is poured into the cup and maintaining the desired ratio of each liquid extracted from its respective container.

| Parameter              | Value                          |
| ---------------------- | ------------------------------ |
| Target volume          | 5 fl oz                        |
| Target volume (metric) | 148 mL                         |
| Measured fill time     | 6.77 seconds                   |
| Flow rate              | 21.877 mL / second             |
| Time per mL            | 45.7 ms / mL                   |
| Pump consistency       | All pumps assumed equivalent   |
| Tubing state           | Pre-filled (continuous column) |

## Beverage Logic

Ultimately, we decided to utilize teas as a versatile mixing substrate, enabling the creation of a wide variety of beverages while simultaneously establishing a precise correlation for emotions. Teas have a longstanding history of mapping emotional states and moods, whether it be through calming teas, uplifting teas, energetic teas, cleansing teas, or others. Additionally, teas are increasingly being embraced as a foundational ingredient in mixology. Furthermore, teas are cost-effective and can be brewed in batches, making them efficient for multiple uses and aligning with our objective of batch production, which we had in mind when we initially began testing the device. Below is a table of the tea ingredients we used, the beverage mixture they correspond to, and the amount of parts one would need to in order to brew that particular batch.

| Emotion    | Beverage Name    | Black Tea | Green Tea | Rooibos Tea | Chamomile Tea | Lemon Tea | Sparkling Water |
| ---------- | ---------------- | --------- | --------- | ----------- | ------------- | --------- | --------------- |
| Happiness  | Golden Glow      | 10        | 10        | 0           | 20            | 40        | 70              |
| Sadness    | Warm Quiet Tea   | 0         | 10        | 25          | 45            | 10        | 60              |
| Stress     | Stillness Cooler | 5         | 40        | 10          | 15            | 5         | 75              |
| Excitement | Citrus Spark     | 30        | 0         | 15          | 0             | 40        | 65              |
| Calm       | Soft Meadow      | 0         | 25        | 15          | 45            | 10        | 55              |
| Surprise   | Crimson Twist    | 10        | 5         | 40          | 10            | 25        | 60              |

![Menu 1](assets/menu1.png)
![Menu 2](assets/menu2.png)

## Coding Stack

Our code can be found at [mixi.py](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/mixi.py), [matrix.yaml](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/matrix.yaml), and [firmware.ino](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Final%20Project/firmware.ino)

_AI Usage:_ Utilized assistance from Cursor for the writing of code.

_Pros:_ Cursor has proven to be overall much more efficient than other LLMs since it analyzes the entirety of the code based into its context and is able to make quick changes without having to backtrack or manually search for the instances of code that need to be changed.

_Cons:_ Since the changes are carried out with it every single prompt command, certain changes that would like to not be preserved versus those that would are hard to discern. The element of version control is an added benefit, but ultimately there needs to be more finer user control over what code elements are changed, and which remain the same.

The primary configuration is loaded from the .yaml (Pi) file and establishes a fixed ordering of ingredients, a closed set of emotion labels, and recipe definitions expressed as proportional arrays. The .py (Pi) file maintains a state loop that handles menu navigation, mode switching, and user actions. It also calls the OpenAI API to engage in text classification for sentiment analysis. When an emotion is selected—either manually or via text classification via ChatGPT—the corresponding recipe array is retrieved, normalized to a fixed total volume by proportional scaling, and serialized to the .ino (Arduino) file to handle the pump logics.

### Dependencies

- Arduino.h
- pyserial
- pyyaml
- numpy
- sounddevice
- SpeechRecognition
- pillow
- openai

![UML Diagram](assets/uml_diagram.png)

_AI Usage:_ Utilized assistance from ChatGPT and PlantUML for diagram layout.

## Form Factor

The exploration of form factors encompassed various image references to arrayed beverage machines or siphon valves, drawing inspiration from tonics, tinctures, and other scent-related confluences. The primary source for the majority of these images was Pinterest.

![Inspiration](assets/insp.png)

_Image Source:_ Images found from Pinterest for keywords: "Beverage Bar," "Siphon Array," "Glass Arrangements," etc.

## Technical Drawings

3D models were created using Rhino and Grasshopper. The primary fabrication method was laser cutting, so models were flattened and transcribed in Adobe Illustrator for the cutting of each face of the device, keeping in mind thickness of materials. These individual faces were subsequently assembled manually using wood adhesives and finished with sandpaper.

### Materials

- 1/16" Balsawood Stock
- 1/4" ID x 3/8" OD Clear Tubing
- Fine Grain Sandpaper
- Black Felt
- Wood Glue

![3D Model 1](assets/3dmodel1.png)
![3Dmodel 2](assets/3dmodel2.png)

## Full Assembly

![View 1](assets/view1.png)
![View 2](assets/view2.png)
![View 3](assets/view3.png)
![View 4](assets/view4.png)
![View 5](assets/view5.png)
![View 6](assets/view6.png)
![View 7](assets/view7.png)
![View 8](assets/view8.png)
![View 9](assets/view9.png)
![View 10](assets/view10.png)

## User Testing

[![User Testing #1 Part 1 Thumbnail](assets/user1_thumb.png)](https://youtu.be/UvjsJDqqkms)  
[Watch User Testing #1 on YouTube](https://youtu.be/UvjsJDqqkms)

[![User Testing #2 Part 1 Thumbnail](assets/user2_thumb.png)](https://youtu.be/hI-nyOW3aA4)  
[Watch User Testing #2 on YouTube](https://youtu.be/hI-nyOW3aA4)

During the showcase, we conducted user testing with a vast range of participants. The majority were from the interactive device design class, while a few participants, particularly those providing detailed feedback, worked in the maker space or adjacent to the Cornell Tech ecosystem. Five batches of iced tea were brewed the previous evening and chilled overnight to create five reservoirs of ice tea, each with an added sparkling water element. Users were given the option to either select a drink from the printed menu or engage with the AI bartender for a recommendation. All interaction elements were prominently displayed and illuminated with a lamp to ensure user awareness of the available options. Team members were also present to assist participants throughout the process.

![Showcase 1](assets/showcase1.png)
![Showcase 2](assets/showcase2.png)
![Showcase 3](assets/showcase3.png)

## Reflections

The interactive device gained significant popularity and was engaged with multiple times throughout the night. Participants were eager to utilize the device, possibly motivated by the prospect of obtaining a personalized beverage at the conclusion of the interaction. The project also received positive feedback regarding its form factor, with appreciation expressed for the wood materials used and the overall compactness of the system. However, some critiques proved to be valuable for future iterations on the project.

One critique suggested implementing a more sophisticated AI taste pipeline. The current setup involves fixing labels to sentiment. One participant expressed interest in creating a system that maps each individual word in the dialogue and transforms it into the subsequent recipe, resulting in a more nuanced and potentially more complex beverage with various competing sentiment vectors influencing the overall taste. A proof of concept for this implementation has been previously prototyped among our team members as a Python Flask app + JavasScript web tool for text dialogue sentiment analysis, which can be found at [sentiment.js](https://github.com/thomknoe/sentiment.js).

Another problem was that most participants remained within the more positively affiliated affects and sentiments, such as happiness or excitement. As a means of encouraging individuals to explore other sentiments or even more complex emotions, changes in the flow or invitation to interaction would need to be considered to ensure that users can engage in the majority of the system’s features rather than remaining limited to a shallow end of the emotional spectrum.

## Conclusions

Toward the end of the showcase, a clear pattern emerged: participants expressed a desire for more direct, self-directed engagement with the system. While initial interactions were mediated by team members—who navigated menus and physically handled the device—participants increasingly sought to operate the system themselves. In response, facilitation was reduced, allowing users to engage independently except where intervention was necessary. This shift highlights a central principle of the course: the importance of intentional physical interaction in design practice. Effective interaction design should support experiences that are not only legible and functional, but also empowering, enabling users to engage with systems in ways that feel comfortable, intuitive, and aligned with their sense of agency. This observation reinforces the value of designing interactions that ultimately recede, allowing users to act freely within them.
