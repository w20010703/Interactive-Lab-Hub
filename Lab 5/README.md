# Observant Systems

<mark> **Collaborators: Thomas Knoepffler, Carrie Wang, Xiaocheng Li, Weiching (Julia) Chen** </mark>

For lab this week, we focus on creating interactive systems that can detect and respond to events or stimuli in the environment of the Pi, like the Boat Detector we mentioned in lecture.
Your **observant device** could, for example, count items, find objects, recognize an event or continuously monitor a room.

This lab will help you think through the design of observant systems, particularly corner cases that the algorithms need to be aware of.

<details>
	<summary><strong>Prep</strong></summary>

## Prep

1.  Install VNC on your laptop if you have not yet done so. This lab will actually require you to run script on your Pi through VNC so that you can see the video stream. Please refer to the [prep for Lab 2](https://github.com/FAR-Lab/Interactive-Lab-Hub/blob/-/Lab%202/prep.md#using-vnc-to-see-your-pi-desktop).
2.  Install the dependencies as described in the [prep document](prep.md).
3.  Read about [OpenCV](https://opencv.org/about/),[Pytorch](https://pytorch.org/), [MediaPipe](https://mediapipe.dev/), and [TeachableMachines](https://teachablemachine.withgoogle.com/).
4.  Read Belloti, et al.'s [Making Sense of Sensing Systems: Five Questions for Designers and Researchers](https://www.cc.gatech.edu/~keith/pubs/chi2002-sensing.pdf).

### For the lab, you will need:

1. Pull the new Github Repo
1. Raspberry Pi
1. Webcam

### Deliverables for this lab are:

1. Show pictures, videos of the "sense-making" algorithms you tried.
1. Show a video of how you embed one of these algorithms into your observant system.
1. Test, characterize your interactive device. Show faults in the detection and how the system handled it.

</details>

<details>
	<summary><strong>Overview</strong></summary>

## Overview

Building upon the paper-airplane metaphor (we're understanding the material of machine learning for design), here are the four sections of the lab activity:

A) [Play](#part-a)

B) [Fold](#part-b)

C) [Flight test](#part-c)

D) [Reflect](#part-d)

</details>

---

<details>
	<summary><strong>Part A</strong></summary>

### Part A

### Play with different sense-making algorithms.

#### Pytorch for object recognition

For this first demo, you will be using PyTorch and running a MobileNet v2 classification model in real time (30 fps+) on the CPU. We will be following steps adapted from [this tutorial](https://pytorch.org/tutorials/intermediate/realtime_rpi.html).

![torch](Readme_files/pyt.gif)

To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md).

Make sure your webcam is connected.

You can check the installation by running:

```
python -c "import torch; print(torch.__version__)"
```

If everything is ok, you should be able to start doing object recognition. For this default example, we use [MobileNet_v2](https://arxiv.org/abs/1801.04381). This model is able to perform object recognition for 1000 object classes (check [classes.json](classes.json) to see which ones.

Start detection by running

```
python infer.py
```

The first 2 inferences will be slower. Now, you can try placing several objects in front of the camera.

Read the `infer.py` script and become familiar with the code. You can change the video resolution and frames per second (FPS). You may also use the weights of the larger pre-trained mobilenet_v3_large model, as described [here](https://pytorch.org/tutorials/intermediate/realtime_rpi.html#model-choices).

#### More classes

[PyTorch supports transfer learning](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html), so you can fine‑tune and transfer learn models to recognize your own objects. It requires extra steps, so we won't cover it here.

For more details on transfer learning and deployment to embedded devices, see Deep Learning on Embedded Systems: A Hands‑On Approach Using Jetson Nano and Raspberry Pi (Tariq M. Arif). [Chapter 10](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch10) covers transfer learning for object detection on desktop, and [Chapter 15](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch15) describes moving models to the Pi using ONNX.

### Machine Vision With Other Tools

The following sections describe tools ([MediaPipe](#mediapipe) and [Teachable Machines](#teachable-machines)).

#### MediaPipe

A established open source and efficient method of extracting information from video streams comes out of Google's [MediaPipe](https://mediapipe.dev/), which offers state of the art face, face mesh, hand pose, and body pose detection.

![Media pipe](Readme_files/mp.gif)

To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md):

Each of the installs will take a while, please be patient. After successfully installing mediapipe, connect your webcam to your Pi and use **VNC to access to your Pi**, open the terminal, and go to Lab 5 folder and run the hand pose detection script we provide:
(**_it will not work if you use ssh from your laptop_**)

```
(venv-ml) pi@ixe00:~ $ cd Interactive-Lab-Hub/Lab\ 5
(venv-ml) pi@ixe00:~ Interactive-Lab-Hub/Lab 5 $ python hand_pose.py
```

Try the two main features of this script: 1) pinching for percentage control, and 2) "[Quiet Coyote](https://www.youtube.com/watch?v=qsKlNVpY7zg)" for instant percentage setting. Notice how this example uses hardcoded positions and relates those positions with a desired set of events, in `hand_pose.py`.

Consider how you might use this position based approach to create an interaction, and write how you might use it on either face, hand or body pose tracking.

(You might also consider how this notion of percentage control with hand tracking might be used in some of the physical UI you may have experimented with in the last lab, for instance in controlling a servo or rotary encoder.)

#### Moondream Vision-Language Model

[Moondream](https://www.ollama.com/library/moondream) is a lightweight vision-language model that can understand and answer questions about images. Unlike the classification models above, Moondream can describe images in natural language and answer specific questions about what it sees.

To use Moondream, first make sure Ollama is running and pull the model:

```bash
ollama pull moondream
```

Then run the simple demo script:

```bash
python moondream_simple.py
```

This will capture an image from your webcam and let you ask questions about it in natural language. Note that vision-language models are slower than classification models (responses may take up to minutes on a Raspberry Pi). There are newer models like [LFM2-VL](https://huggingface.co/LiquidAI/LFM2-VL-450M-GGUF), but many are very recent and not yet optimized for embedded devices.

**Design consideration**: Think about how slower response times change your interaction design. What kinds of observant systems benefit from thoughtful, delayed responses rather than real-time classification? Consider systems that monitor over longer time periods or provide periodic summaries rather than instant feedback.

#### Teachable Machines

Google's [TeachableMachines](https://teachablemachine.withgoogle.com/train) is very useful for prototyping with the capabilities of machine learning. We are using [a python package](https://github.com/MeqdadDev/teachable-machine-lite) with tensorflow lite to simplify the deployment process.

![Tachable Machines Pi](Readme_files/tml_pi.gif)

To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md):

After installation, connect your webcam to your Pi and use **VNC to access to your Pi**, open the terminal, and go to Lab 5 folder and run the example script:
(**_it will not work if you use ssh from your laptop_**)

```
(venv-tml) pi@ixe00:~ Interactive-Lab-Hub/Lab 5 $ python tml_example.py
```

Next train your own model. Visit [TeachableMachines](https://teachablemachine.withgoogle.com/train), select Image Project and Standard model. The raspberry pi 4 is capable to run not just the low resource models. Second, use the webcam on your computer to train a model. _Note: It might be advisable to use the pi webcam in a similar setting you want to deploy it to improve performance._ For each class try to have over 150 samples, and consider adding a background or default class where you have nothing in view so the model is trained to know that this is the background. Then create classes based on what you want the model to classify. Lastly, preview and iterate. Finally export your model as a 'Tensorflow lite' model. You will find an '.tflite' file and a 'labels.txt' file. Upload these to your pi (through one of the many ways such as [scp](https://www.raspberrypi.com/documentation/computers/remote-access.html#using-secure-copy), sftp, [vnc](https://help.realvnc.com/hc/en-us/articles/360002249917-VNC-Connect-and-Raspberry-Pi#transferring-files-to-and-from-your-raspberry-pi-0-6), or a connected visual studio code remote explorer).
![Teachable Machines Browser](Readme_files/tml_browser.gif)
![Tensorflow Lite Download](Readme_files/tml_download-model.png)

Include screenshots of your use of Teachable Machines, and write how you might use this to create your own classifier. Include what different affordances this method brings, compared to the OpenCV or MediaPipe options.

#### (Optional) Legacy audio and computer vision observation approaches

In an earlier version of this class students experimented with observing through audio cues. Find the material here:
[Audio_optional/audio.md](Audio_optional/audio.md).
Teachable machines provides an audio classifier too. If you want to use audio classification this is our suggested method.

In an earlier version of this class students experimented with foundational computer vision techniques such as face and flow detection. Techniques like these can be sufficient, more performant, and allow non discrete classification. Find the material here:
[CV_optional/cv.md](CV_optional/cv.md).

</details>

<details>
	<summary><strong>Part B</strong></summary>

### Part B

### Construct a simple interaction.

- Pick one of the models you have tried, and experiment with prototyping an interaction.
- This can be as simple as the boat detector shown in lecture.
- Try out different interaction outputs and inputs.

</details>

**\*\*\*Describe and detail the interaction, as well as your experimentation here.\*\*\***

<mark> This lab is inspired by [Gene Kogan's Experiments with Style Transfer](https://genekogan.com/works/style-transfer/), incorporating new advancements in the style-transfer TensorFlow model and Raspberry Pi hardware. This is a relativley old exploration and application, but there is still more to be discovered or created. </mark>

<mark>We used TensorFlow's [arbitrary-image-stylization-v1](https://www.kaggle.com/models/google/arbitrary-image-stylization-v1), both 256-fp16 prediction and transfer models. Provided by Google.</mark>

<mark> This lab is both an experiment in computational optimization, an artistic exploration with the nature of computer vision via style transfer, and the discourse created between vision and computation. The goal of this lab is to be able to capture the "artistic visuality" (i.e., the style) within classic paintings or textures, and transcribe them to live video feed through the Pi. The final deliverable is to create a narrative piece that will use style transfer for still and moving images, or the montage style of filmmaking (e.g., [Le Jetée (1962)](https://www.youtube.com/watch?v=Pf4AY_DI9BE). This film is also the main artistic inspiration for this project).</mark>

![Le Jetee](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/le_jetee.jpg)

<mark> _**Image Source:** Le Jetée (1962)_ </mark>

<mark> We began with loading up the Pi with modern art preset images that would serve as examples for style transfer. </mark>

<p align="center">
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/kandinsky.jpg" alt="Kandinsky" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/lichtenstein.jpg" alt="Lichtenstein" width="49.5%"/>
    <img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/matisse.jpg" alt="Matisse" width="49.5%"/>
    <img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/mondrian.jpg" alt="Mondrian" width="49.5%"/>
    <img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/monet.jpg" alt="Monet" width="49.5%"/>
    <img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/munch.jpg" alt="Munch" width="49.5%"/>
</p>

<mark> _**Image Source(s):** Kandinsky, Composition VII (1913); Roy Lichtenstein, Drowning Girl (1963); Henri Matisse, The Dance (1910); Piet Mondrian, Composition with Red, Blue, and Yellow (1930); Claude Monet, Water Lilies (1914-26); Edvard Munch, The Scream (1893)._ </mark>

<mark> From there, we loaded up style transfer models from TensorFlow onto the Pi and mapped the secondary input image to be the WebCam feed. We remapped the vector space so that it could accommodate the camera feed dimensions. We experimented with various output dimensions and decided on a relatively small resolution of 380 x 285, just so that the video can efficiently process at a higher frame rate. We also chose to use the 256-fp16 version of the model, which proved to be faster than the initial model we downloaded, which was the quantized verison. Our first FPS rate was around 2. Our final FPS rate ranged between 6-7. </mark>

<mark> Our code can be found at [stylecam_hdmi.py](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/style/stylecam_hdmi.py) </mark>

<mark> _**AI Usage:** Utilized assistance from ChatGPT for the writing of code._ </mark>

<mark> _**Pros:** The code was suprisingly quick to generate, considering this has been has always been a difficult model to train, load, and use._ </mark>

<mark> _**Cons:** The first generation provided the lowest resolution and efficiency model, which kept the FPS at around 2. This was not an ideal framerate for motion capture video. More prompting was needed to find a new model and ultimatley optimize the resolution._ </mark>

<mark> In order to use this code, one would need to run the Pi GUI through an HDMI or remote VNC connection. </mark>

![Electronics Setup](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/Electronics_Setup.jpg)

<p align="center">
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_1.jpg" alt="Style 1" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_2.jpg" alt="Style 2" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_3.jpg" alt="Style 3" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_4.jpg" alt="Style 4" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_5.jpg" alt="Style 5" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/style_6.jpg" alt="Style 6" width="49.5%"/>
</p>

<details>
	<summary><strong>Part C</strong></summary>

### Part C

### Test the interaction prototype

Now flight test your interactive prototype and **note down your observations**:
For example:

1. When does it what it is supposed to do?
1. When does it fail?
1. When it fails, why does it fail?
1. Based on the behavior you have seen, what other scenarios could cause problems?
1. Are they aware of the uncertainties in the system?
1. How bad would they be impacted by a miss classification?
1. How could change your interactive system to address this?
1. Are there optimizations you can try to do on your sense-making algorithm.

</details>

**\*\*\*Think about someone using the system. Describe how you think this will work.\*\*\***

<mark> Now that the code worked on the laptop, we decided to fully move the set up to the Pi by mapping the video feed onto the Mini piTFT screen. Despite the new resolution, the frame rate remained about the same, ranging from 6-7.</mark>

<mark> This will be important as the final device will be a portable, observing handheld setup. It would be a combination of both a camera and a viewfinder, combining the stylized images that are input by the user, and showcasing a snapshot of the environment around them from the Mini piTFT screen. Depending on how users will want to interact; either we make it a live feed that offers a window to the stylized realm, or we can make it a pure camera that allows users to take individual pictures of the world around them, and display it. Both of these designs would depend on both user preference and computational efficiency, whether the video feed will run throughout a long interaction.</mark>

<mark> Our code can be found at [stylecam_pitft.py](https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/style/stylecam_pitft.py) </mark>

<mark> _**AI Usage:** Utilized assistance from ChatGPT for the writing of code._ </mark>

<mark> _**Pros:** The code was able to accommodate the new vector space easily and required only the context of the Mini PiTFT product page to find the appropriate remapping, which is usually a difficult and tedious task._ </mark>

<mark> _**Cons:** It was difficult to find the model that would best suit the Pi. We ultimately found an appropriate model through Google because the archived CDN downloads that ChatGPT tried to provide were all broken or returned a 404. Not a single one provided by ChatGPT seems to work, which means that most models provided in chat could not be used._ </mark>

<p align="center">
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/piTFT_1.jpg" alt="piTFT 1" width="33%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/piTFT_2.jpg" alt="piTFT 2" width="33%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/piTFT_3.jpg" alt="piTFT 3" width="33%"/>
</p>

<details>
	<summary><strong>Part D</strong></summary>

### Part D

### Characterize your own Observant system

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:

- What can you use X for?
- What is a good environment for X?
- What is a bad environment for X?
- When will X break?
- When it breaks how will X break?
- What are other properties/behaviors of X?
- How does X feel?

</details>

**\*\*\*Include a short video demonstrating the answers to these questions.\*\*\***

<mark> The video feed is able to run relatively fluently, making it a technical possibility for this lab to include stylized video. User testing and enclosure designs are underway, as well as storyboards for an interaction film. </mark>

<p align="center">
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/demo_1.gif" alt="Demo 1" width="49.5%"/>
	<img src="https://github.com/thomknoe/INFO-5345/blob/Fall2025/Lab%205/Images/demo_2.gif" alt="Demo 2" width="49.5%"/>
</p>

<details>
	<summary><strong>Part 2</strong></summary>

### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

</details>

**\*\*\*Include a short video demonstrating the finished result.\*\*\***
