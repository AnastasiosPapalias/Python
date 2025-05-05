import tkinter as tk
import random
import json
import os
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk

class MindfulnessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Mindfulness Practice")
        self.root.geometry("800x700")
        self.root.configure(bg="#f5f5f7")
        
        # Set app icon if available
        self.root.iconbitmap('mindfulness.ico') if os.path.exists('mindfulness.ico') else None
        
        # Initialize style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f7")
        self.style.configure("TButton", 
                            background="#4d94ff", 
                            foreground="black", 
                            font=("Helvetica", 12, "bold"),
                            padding=10)
        self.style.map("TButton",
                     background=[("active", "#80b5ff")])
        
        # Load content from JSON or create if not exists
        self.data_file = "mindfulness_content.json"
        self.user_progress_file = "mindfulness_progress.json"
        self.completed_lessons = self.load_user_progress()
        self.content = self.load_or_create_content()
        self.current_content = None
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="Daily Mindfulness", 
            font=("Helvetica", 24, "bold"),
            bg="#f5f5f7",
            fg="#333333"
        )
        self.title_label.pack()
        
        self.date_label = tk.Label(
            self.header_frame, 
            text=datetime.now().strftime("%A, %B %d, %Y"), 
            font=("Helvetica", 12, "italic"),
            bg="#f5f5f7",
            fg="#666666"
        )
        self.date_label.pack(pady=(0, 10))
        
        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Theory section
        self.theory_label = tk.Label(
            self.content_frame, 
            text="Today's Theory:", 
            font=("Helvetica", 16, "bold"),
            anchor="w",
            bg="#f5f5f7",
            fg="#333333"
        )
        self.theory_label.pack(fill=tk.X, pady=(0, 5))
        
        # Theory content (scrollable)
        self.theory_text = scrolledtext.ScrolledText(
            self.content_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=8,
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#333333",
            padx=10,
            pady=10
        )
        self.theory_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.theory_text.configure(state="disabled")
        
        # Task section
        self.task_label = tk.Label(
            self.content_frame, 
            text="Today's Task:", 
            font=("Helvetica", 16, "bold"),
            anchor="w",
            bg="#f5f5f7",
            fg="#333333"
        )
        self.task_label.pack(fill=tk.X, pady=(0, 5))
        
        # Task content (scrollable)
        self.task_text = scrolledtext.ScrolledText(
            self.content_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=6,
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#333333",
            padx=10,
            pady=10
        )
        self.task_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.task_text.configure(state="disabled")
        
        # Lesson section
        self.lesson_label = tk.Label(
            self.content_frame, 
            text="Today's Lesson:", 
            font=("Helvetica", 16, "bold"),
            anchor="w",
            bg="#f5f5f7",
            fg="#333333"
        )
        self.lesson_label.pack(fill=tk.X, pady=(0, 5))
        
        # Lesson content (scrollable)
        self.lesson_text = scrolledtext.ScrolledText(
            self.content_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=8,
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#333333",
            padx=10,
            pady=10
        )
        self.lesson_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.lesson_text.configure(state="disabled")
        
        # Button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Mark as complete button
        self.complete_button = ttk.Button(
            self.button_frame, 
            text="Mark Today as Complete", 
            command=self.mark_as_complete
        )
        self.complete_button.pack(side=tk.LEFT, padx=5)
        
        # Next day button
        self.next_button = ttk.Button(
            self.button_frame, 
            text="Preview Tomorrow", 
            command=self.load_random_content
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Progress button
        self.progress_button = ttk.Button(
            self.button_frame, 
            text="View Progress", 
            command=self.show_progress
        )
        self.progress_button.pack(side=tk.LEFT, padx=5)
        
        # Reflection section
        self.reflection_frame = ttk.Frame(self.main_frame)
        self.reflection_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.reflection_label = tk.Label(
            self.reflection_frame, 
            text="Your Reflections:", 
            font=("Helvetica", 14, "bold"),
            anchor="w",
            bg="#f5f5f7",
            fg="#333333"
        )
        self.reflection_label.pack(fill=tk.X, pady=(0, 5))
        
        self.reflection_text = scrolledtext.ScrolledText(
            self.reflection_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=5,
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#333333",
            padx=10,
            pady=10
        )
        self.reflection_text.pack(fill=tk.BOTH, expand=True)
        
        # Save reflection button
        self.save_reflection_button = ttk.Button(
            self.reflection_frame, 
            text="Save Reflection", 
            command=self.save_reflection
        )
        self.save_reflection_button.pack(anchor="e", pady=(10, 0))
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text="", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg="#e6e6e6",
            fg="#333333"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load today's content on startup
        self.load_todays_content()

    def load_or_create_content(self):
        """Load content from JSON file or create default content if file doesn't exist"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, create new content
                content = self.create_default_content()
                self.save_content(content)
                return content
        else:
            # Create default content
            content = self.create_default_content()
            self.save_content(content)
            return content

    def create_default_content(self):
        """Create default mindfulness content"""
        return {
            "daily_content": [
                {
                    "id": 1,
                    "theory": (
                        "Mindfulness is the practice of deliberately paying attention to the present moment with an attitude "
                        "of openness and curiosity. It involves observing your thoughts, feelings, bodily sensations, and "
                        "the surrounding environment without judgment.\n\n"
                        "Research shows that regular mindfulness practice can reduce stress and anxiety while improving focus, "
                        "emotional regulation, and overall well-being. The practice has roots in ancient contemplative traditions "
                        "but has been adapted for modern contexts based on scientific evidence."
                    ),
                    "task": (
                        "Find a quiet place where you won't be disturbed for 5 minutes. Sit comfortably with your back straight "
                        "and your body relaxed. Focus your attention on your breath—the sensation of air flowing in and out of "
                        "your nostrils or the rising and falling of your chest or abdomen.\n\n"
                        "When your mind wanders (which is completely normal), gently bring your attention back to your breath. "
                        "Try not to judge yourself when this happens—simply notice it and refocus."
                    ),
                    "lesson": (
                        "The essence of mindfulness is developing awareness without judgment. Every time you notice your mind "
                        "has wandered and you bring it back to your breath, you're strengthening your mindfulness muscle.\n\n"
                        "Being present isn't about achieving a perfect state of focus. It's about noticing when you're not "
                        "present and gently returning to awareness, again and again. This process of returning is the practice.\n\n"
                        "As you continue this daily practice, you may notice that the quality of your attention gradually "
                        "changes, allowing you to be more fully present in all aspects of your life."
                    )
                },
                {
                    "id": 2,
                    "theory": (
                        "Our breathing is constantly with us, yet we rarely pay attention to it. The breath serves as an "
                        "anchor to the present moment and a bridge between mind and body. When we focus on our breathing, "
                        "we naturally pull ourselves away from rumination about the past or worries about the future.\n\n"
                        "Conscious breathing activates the parasympathetic nervous system (our 'rest and digest' response), "
                        "which counteracts the stress response and promotes relaxation. This physiological shift can happen "
                        "in just a few mindful breaths."
                    ),
                    "task": (
                        "Today, practice the 4-7-8 breathing technique:\n\n"
                        "1. Sit comfortably and close your eyes\n"
                        "2. Inhale quietly through your nose for a count of 4\n"
                        "3. Hold your breath for a count of 7\n"
                        "4. Exhale completely through your mouth for a count of 8\n"
                        "5. Repeat this cycle 4 times\n\n"
                        "Try this technique once in the morning and once in the evening. You can also use it whenever you "
                        "feel stressed or anxious during the day."
                    ),
                    "lesson": (
                        "The breath is always available as a tool for centering yourself. You don't need any special equipment "
                        "or setting to practice breath awareness—it can be done anywhere, anytime.\n\n"
                        "Different breathing patterns have different effects on your nervous system. Slow, deep breathing "
                        "calms the mind and body, while rapid, shallow breathing often accompanies and intensifies stress.\n\n"
                        "By consciously changing your breathing pattern, you can influence your emotional state and thought "
                        "patterns. This makes breath awareness one of the most practical and powerful mindfulness tools."
                    )
                },
                {
                    "id": 3,
                    "theory": (
                        "Our minds naturally produce thoughts—it's what they're designed to do. Mindfulness isn't about "
                        "stopping thoughts but about changing our relationship with them. By observing thoughts without "
                        "getting caught up in them, we develop what psychologists call 'metacognitive awareness'—the ability "
                        "to experience thoughts as mental events rather than absolute truths.\n\n"
                        "This shift in perspective creates space between ourselves and our thoughts, giving us more choice "
                        "in how we respond to them. Research shows this practice can be particularly helpful for conditions "
                        "like depression and anxiety, which often involve being trapped in negative thought patterns."
                    ),
                    "task": (
                        "Spend 10 minutes practicing thought observation:\n\n"
                        "1. Sit comfortably in a quiet place\n"
                        "2. Close your eyes and take a few deep breaths to center yourself\n"
                        "3. When thoughts arise, mentally label them: 'thinking,' 'remembering,' 'planning,' 'worrying,' etc.\n"
                        "4. Imagine your thoughts as clouds passing across the sky of your mind\n"
                        "5. Don't try to change your thoughts—simply observe them as they come and go\n"
                        "6. When you notice you've been caught up in a thought, gently return to observing\n\n"
                        "After the practice, take a moment to reflect on what types of thoughts were most common."
                    ),
                    "lesson": (
                        "Thoughts are not facts, even though they often feel like the truth. When we identify too strongly "
                        "with our thoughts, we can become trapped in limiting beliefs or negative spirals.\n\n"
                        "The phrase 'I am having the thought that...' can help create distance between you and your thoughts. "
                        "For example, instead of 'I'm a failure,' notice 'I'm having the thought that I'm a failure.'\n\n"
                        "With practice, you'll discover that you are not your thoughts—you are the awareness that observes "
                        "thoughts. This awareness remains stable even as thoughts and feelings constantly change."
                    )
                },
                {
                    "id": 4,
                    "theory": (
                        "Our bodies constantly provide information about our emotional and mental states, but we often "
                        "ignore these signals. The body scan is a systematic practice of bringing awareness to physical "
                        "sensations throughout the body.\n\n"
                        "Through this practice, we learn to notice bodily sensations without judgment or the need to change "
                        "them. This improves our interoceptive awareness—the ability to sense internal bodily states—which "
                        "is associated with better emotional regulation and decision-making."
                    ),
                    "task": (
                        "Find a quiet place where you can lie down comfortably for 15 minutes.\n\n"
                        "1. Lie on your back with arms relaxed at your sides\n"
                        "2. Close your eyes and take a few deep breaths\n"
                        "3. Bring your awareness to your feet, noticing any sensations\n"
                        "4. Slowly move your attention up through your legs, pelvis, abdomen, chest, back, hands, arms, shoulders, neck, and head\n"
                        "5. For each area, spend about 30 seconds simply observing sensations without trying to change them\n"
                        "6. If your mind wanders, gently bring it back to the body part you were focusing on\n\n"
                        "Notice if there are areas of tension or areas where you felt particularly relaxed."
                    ),
                    "lesson": (
                        "Many of us live predominantly in our heads, disconnected from the wisdom of our bodies. The body often "
                        "registers emotional responses before they reach conscious awareness.\n\n"
                        "Physical sensations can serve as early warning signs of stress or emotional reactions. For example, "
                        "tension in the shoulders or a knot in the stomach might signal anxiety before you consciously recognize the feeling.\n\n"
                        "Regular body scan practice helps you recognize and release tension that you may unconsciously hold. "
                        "This can lead to better stress management, improved sleep, and a greater sense of embodied presence."
                    )
                },
                {
                    "id": 5,
                    "theory": (
                        "Mindful eating involves bringing full awareness to the experience of eating and drinking. This practice "
                        "helps us develop a healthier relationship with food and recognize hunger and fullness cues more accurately.\n\n"
                        "In our busy lives, eating often becomes automatic or distracted. We might eat while working, scrolling through "
                        "social media, or watching TV, barely noticing what or how much we're consuming. Mindful eating counteracts "
                        "this disconnection by engaging all our senses in the eating experience."
                    ),
                    "task": (
                        "Choose one meal today to eat mindfully.\n\n"
                        "1. Before eating, take a moment to appreciate the appearance of your food\n"
                        "2. Notice the colors, shapes, and arrangement on your plate\n"
                        "3. Take a moment to smell your food, noticing any aromas\n"
                        "4. Take small bites and chew thoroughly, noticing the flavors and textures\n"
                        "5. Put down your utensils between bites\n"
                        "6. Notice the sensations of hunger and fullness in your body\n"
                        "7. Eat without distractions—no TV, phone, or reading\n\n"
                        "After the meal, reflect on how this experience differed from your usual eating habits."
                    ),
                    "lesson": (
                        "Eating mindfully helps us distinguish between physical hunger and emotional hunger. Physical hunger "
                        "develops gradually and can be satisfied with various foods, while emotional hunger comes on suddenly "
                        "and often craves specific comfort foods.\n\n"
                        "The satisfaction we derive from food isn't just about quantity but also about the quality of our "
                        "attention. When we eat mindfully, we often need less food to feel satisfied because we're fully "
                        "experiencing what we eat.\n\n"
                        "Mindful eating isn't about perfect eating or rigid rules—it's about bringing awareness and presence "
                        "to our relationship with food. This awareness naturally leads to healthier choices without the need "
                        "for strict diets or self-judgment."
                    )
                },
                {
                    "id": 6,
                    "theory": (
                        "Walking meditation combines physical movement with mental awareness, making it an excellent practice "
                        "for those who find seated meditation challenging. In walking meditation, the focus is on the sensations "
                        "of walking rather than reaching a destination.\n\n"
                        "This practice bridges the gap between formal meditation and everyday life, helping us bring mindfulness "
                        "into motion. It's particularly effective for working with restlessness or agitation, as it gives the "
                        "body something to do while cultivating mental presence."
                    ),
                    "task": (
                        "Find a quiet path or area where you can walk slowly for 10-15 minutes without interruption.\n\n"
                        "1. Stand still and become aware of your body, feeling the weight on your feet\n"
                        "2. Begin walking at a slower pace than normal\n"
                        "3. Pay attention to the lifting, moving, and placing of each foot\n"
                        "4. Notice the shifting of weight and the sensations in your legs and feet\n"
                        "5. When your mind wanders, gently bring it back to the sensations of walking\n"
                        "6. You can use gentle labels like 'lifting,' 'moving,' 'placing' if it helps maintain focus\n\n"
                        "Notice how different this feels from your usual walking pace and style."
                    ),
                    "lesson": (
                        "Walking is something most of us do every day without much awareness. By bringing mindfulness to this "
                        "routine activity, we practice bringing presence into everyday life.\n\n"
                        "In our goal-oriented culture, we're often focused on getting somewhere rather than being present for "
                        "the journey. Walking meditation invites us to focus on the process rather than the destination.\n\n"
                        "This practice reminds us that mindfulness isn't confined to quiet rooms or meditation cushions—it can "
                        "be integrated into all our movements and activities throughout the day."
                    )
                },
                {
                    "id": 7,
                    "theory": (
                        "Emotions provide valuable information, but we often either suppress them or become overwhelmed by them. "
                        "Mindfulness of emotions involves acknowledging feelings without judgment or reactivity.\n\n"
                        "Research shows that naming emotions activates the prefrontal cortex and reduces activity in the amygdala, "
                        "helping us respond rather than react. This practice helps us understand that emotions, like thoughts, "
                        "are temporary experiences rather than permanent conditions or personal identities."
                    ),
                    "task": (
                        "Practice this exercise whenever a strong emotion arises today.\n\n"
                        "1. When you notice an emotional reaction, pause\n"
                        "2. Take three conscious breaths\n"
                        "3. Name the emotion: 'anger,' 'sadness,' 'joy,' 'fear,' etc.\n"
                        "4. Locate where you feel the emotion in your body\n"
                        "5. Observe the physical sensations with curiosity: temperature, movement, texture, etc.\n"
                        "6. Allow the emotion to be present without trying to change it\n"
                        "7. Notice how the emotion naturally changes over time\n\n"
                        "At the end of the day, reflect on which emotions you noticed and how the practice affected your experience."
                    ),
                    "lesson": (
                        "Emotions exist on a spectrum from subtle to intense. Catching emotions when they're still subtle gives "
                        "you more choices in how to respond. With practice, you can develop earlier awareness of emotional states.\n\n"
                        "The phrase 'name it to tame it' describes how labeling emotions helps reduce their intensity. Naming an "
                        "emotion activates the thinking brain, which can modulate the emotional brain.\n\n"
                        "All emotions contain valuable information and energy. Even difficult emotions like anger, fear, or sadness "
                        "have important messages and can motivate constructive action when approached mindfully."
                    )
                },
                {
                    "id": 8,
                    "theory": (
                        "Self-compassion involves treating ourselves with the same kindness we would offer to a good friend. "
                        "It combines mindfulness with self-kindness and recognition of our common humanity.\n\n"
                        "Research by Dr. Kristin Neff shows that self-compassion is strongly associated with psychological wellbeing, "
                        "resilience, and healthier relationships. Unlike self-criticism, which undermines motivation, "
                        "self-compassion provides a secure base for growth and change."
                    ),
                    "task": (
                        "Practice this self-compassion exercise when you notice self-criticism or difficult emotions today.\n\n"
                        "1. Notice when you're struggling or being hard on yourself\n"
                        "2. Place your hand on your heart or another soothing place\n"
                        "3. Acknowledge your pain: 'This is a moment of suffering'\n"
                        "4. Recognize your shared humanity: 'Suffering is part of life; I'm not alone in this'\n"
                        "5. Offer yourself kindness: 'May I be kind to myself in this moment'\n"
                        "6. Ask yourself: 'What do I need to hear right now?' or 'How can I care for myself in this moment?'\n\n"
                        "For deeper practice, write a compassionate letter to yourself about a current struggle, as if you were writing to a dear friend."
                    ),
                    "lesson": (
                        "Self-compassion is not self-pity or self-indulgence. It's about holding your pain with awareness and kindness "
                        "while maintaining a sense of perspective. Self-compassion actually leads to greater personal responsibility and motivation.\n\n"
                        "The three components of self-compassion are: mindfulness (being aware of suffering without exaggeration or suppression), "
                        "common humanity (recognizing that imperfection is part of the shared human experience), and self-kindness "
                        "(treating yourself with care rather than harsh judgment).\n\n"
                        "We often speak to ourselves in ways we would never speak to others. Becoming aware of your inner dialogue "
                        "is the first step toward developing a more compassionate relationship with yourself."
                    )
                },
                {
                    "id": 9,
                    "theory": (
                        "Our attention is constantly pulled in multiple directions by devices, notifications, and busy schedules. "
                        "Single-tasking—focusing on one activity at a time—is a form of mindfulness practice that counteracts this fragmentation.\n\n"
                        "Research shows that multitasking is largely a myth. What we call 'multitasking' is actually rapid task-switching, "
                        "which reduces efficiency and increases stress. When we give our full attention to one task, we not only perform "
                        "better but also experience greater satisfaction."
                    ),
                    "task": (
                        "Choose one activity today to practice single-tasking.\n\n"
                        "1. Select an activity you normally rush through or do while multitasking (e.g., showering, cooking, cleaning)\n"
                        "2. Clear away distractions (put your phone in another room, turn off music/TV)\n"
                        "3. Set an intention to give this activity your full attention\n"
                        "4. Engage all your senses in the experience\n"
                        "5. When your mind wanders to other tasks or worries, gently bring it back\n"
                        "6. Notice the urge to hurry or do something else simultaneously\n\n"
                        "After completing the activity, reflect on how the experience differed from your usual approach."
                    ),
                    "lesson": (
                        "Single-tasking is a radical act in a culture that values productivity above all else. By choosing to do one thing "
                        "at a time, you reclaim your attention from the constant pull of distractions.\n\n"
                        "The quality of our attention determines the quality of our experience. When we're fully present for an "
                        "activity—even a mundane one—we discover richness and depth that we miss when our attention is divided.\n\n"
                        "Single-tasking doesn't mean you accomplish less; often, you accomplish more with greater accuracy and less stress. "
                        "It's about working with your brain's natural capabilities rather than against them."
                    )
                },
                {
                    "id": 10,
                    "theory": (
                        "Gratitude is the quality of appreciating what we have rather than focusing on what we lack. As a mindfulness "
                        "practice, gratitude involves consciously recognizing the good in our lives and savoring positive experiences.\n\n"
                        "Our brains have a negativity bias, making us more sensitive to unpleasant experiences than pleasant ones. "
                        "Gratitude practice counteracts this tendency by intentionally directing attention to positive aspects of experience."
                    ),
                    "task": (
                        "Set aside 10 minutes for this gratitude practice.\n\n"
                        "1. Find a quiet space and take a few mindful breaths\n"
                        "2. Reflect on three things you're grateful for today—they can be simple everyday experiences\n"
                        "3. For each item, write down:\n"
                        "   - What specifically you appreciate\n"
                        "   - Why you value this\n"
                        "   - How it enriches your life\n"
                        "4. As you write about each item, allow yourself to fully feel the gratitude in your body\n"
                        "5. Consider expressing appreciation directly if your gratitude involves other people\n\n"
                        "Notice how focusing on gratitude affects your mood and perspective."
                    ),
                    "lesson": (
                        "Gratitude shifts our focus from what's wrong to what's right. This doesn't mean ignoring problems or "
                        "challenges, but rather balancing our awareness to include the positive aspects of experience that we often overlook.\n\n"
                        "We can cultivate gratitude even during difficult times. Sometimes the most powerful gratitude practice comes "
                        "from finding small things to appreciate in the midst of challenges.\n\n"
                        "Regular gratitude practice actually changes the brain over time, strengthening neural pathways that predispose "
                        "us to notice the good. This creates a positive cycle: the more we practice gratitude, the more we find to be grateful for."
                    )
                },
                {
                    "id": 11,
                    "theory": (
                        "Mindfulness in daily activities involves bringing awareness to routine tasks we normally do on autopilot. "
                        "By choosing everyday activities as opportunities for practice, we extend mindfulness beyond formal meditation.\n\n"
                        "Research indicates that this kind of informal practice may be just as important as formal meditation for "
                        "deriving the benefits of mindfulness. It helps us live more fully in each moment rather than operating on autopilot."
                    ),
                    "task": (
                        "Choose one routine activity to perform mindfully today. Options include:\n\n"
                        "- Brushing your teeth\n"
                        "- Washing dishes\n"
                        "- Taking a shower\n"
                        "- Drinking tea or coffee\n"
                        "- Commuting\n\n"
                        "For your chosen activity:\n"
                        "1. Slow down slightly and bring full attention to the physical sensations\n"
                        "2. Notice the movements of your body, the sounds, smells, and textures\n"
                        "3. When your mind wanders, gently bring it back to the sensory experience\n"
                        "4. Approach the activity with curiosity, as if doing it for the first time\n\n"
                        "Reflect on how this mindful approach changed your experience of a familiar activity."
                    ),
                    "lesson": (
                        "Many of life's precious moments occur during ordinary activities that we rush through without awareness. "
                        "Mindfulness in daily life is about showing up for these moments rather than sleepwalking through them.\n\n"
                        "You don't need to dramatically slow down or change your routine to practice mindfulness in daily life. "
                        "Even bringing 10% more awareness to ordinary activities can significantly enhance your experience.\n\n"
                        "The distinction between formal meditation and daily life starts to dissolve with practice. Eventually, "
                        "life itself becomes the meditation, with each activity an opportunity to be present and aware."
                    )
                },
                {
                    "id": 12,
                    "theory": (
                        "Technology offers many benefits but can also fragment our attention and increase stress. Digital mindfulness "
                        "involves bringing awareness to our relationship with devices and media.\n\n"
                        "Our devices are designed to capture and hold attention through notifications, infinite scrolling, and "
                        "algorithm-driven content. This can lead to 'digital autopilot'—using technology without conscious awareness or intention.\n\n"
                        "Research shows that mindless digital consumption is associated with increased stress, anxiety, and dissatisfaction. "
                        "Digital mindfulness helps us use technology intentionally as a tool rather than being controlled by it."
                    ),
                    "task": (
                        "Today, practice digital mindfulness with these exercises:\n\n"
                        "1. Technology Check-In (5 minutes):\n"
                        "   - Before reaching for your phone or opening your laptop, pause\n"
                        "   - Take three conscious breaths\n"
                        "   - Ask yourself: 'Why am I using this device right now? Is this necessary or habitual?'\n"
                        "   - Set a clear intention for your technology use\n\n"
                        "2. Mindful Media Consumption (ongoing):\n"
                        "   - Before consuming content, ask: 'Is this worthy of my attention?'\n"
                        "   - Notice how different types of content affect your mood and energy\n"
                        "   - Practice single-tasking: one device, one activity at a time\n\n"
                        "3. Digital Boundaries (experiment):\n"
                        "   - Designate one hour today as a device-free zone\n"
                        "   - Turn off non-essential notifications\n"
                        "   - Create physical distance between yourself and devices during meals or conversations\n\n"
                        "At the end of the day, reflect on how these practices affected your relationship with technology."
                    ),
                    "lesson": (
                        "Technology itself is neither good nor bad—it's how we use it that matters. Digital mindfulness is not "
                        "about rejecting technology but about using it intentionally and in alignment with our values.\n\n"
                        "The constant stream of information and stimulation from our devices can keep us in a state of "
                        "continuous partial attention, where we're never fully present for anything. Creating boundaries around "
                        "technology use helps restore our capacity for deep attention and presence.\n\n"
                        "Just as we can bring mindfulness to breathing or eating, we can bring mindfulness to our digital "
                        "consumption. This awareness naturally leads to more conscious choices about when, how, and why we use technology."
                    )
                },
                {
                    "id": 13,
                    "theory": (
                        "Loving-kindness meditation (Metta) cultivates unconditional goodwill toward ourselves and others. "
                        "While many mindfulness practices focus on awareness, loving-kindness actively develops positive emotions.\n\n"
                        "This practice counteracts our negativity bias—our tendency to focus more on negative experiences than positive "
                        "ones. It expands our circle of concern from ourselves to all beings, fostering a sense of connection and compassion."
                    ),
                    "task": (
                        "Find a comfortable seated position for 15 minutes.\n\n"
                        "1. Begin by focusing on your breath and heart area\n"
                        "2. Bring to mind someone who naturally evokes feelings of love (a child, pet, or dear friend)\n"
                        "3. Silently repeat these phrases, directing them first to yourself:\n"
                        "   - May I be safe and protected\n"
                        "   - May I be happy and peaceful\n"
                        "   - May I be healthy and strong\n"
                        "   - May I live with ease\n"
                        "4. Next, direct these wishes to your loved one, then to a neutral person, then to someone difficult\n"
                        "5. Finally, extend these wishes to all beings everywhere\n\n"
                        "Notice any resistance that arises, especially when directing loving-kindness toward yourself or difficult people."
                    ),
                    "lesson": (
                        "Loving-kindness is a skill that can be developed with practice. Even if the feelings don't come easily at first, "
                        "the intention itself is transformative. With regular practice, genuine feelings of warmth and care often naturally emerge.\n\n"
                        "Starting with yourself or an easy person creates a foundation for extending loving-kindness to more challenging "
                        "relationships. The practice gradually expands in widening circles, but each stage is important.\n\n"
                        "Loving-kindness doesn't mean approving of harmful behavior or bypassing accountability. It means recognizing "
                        "our shared humanity and wishing for well-being at a fundamental level, which can coexist with appropriate boundaries."
                    )
                },
                {
                    "id": 14,
                    "theory": (
                        "Nature provides an ideal setting for mindfulness practice, offering rich sensory experiences and a sense "
                        "of connection beyond ourselves. Natural environments naturally evoke mindful awareness.\n\n"
                        "Research shows that time in nature reduces stress hormones, lowers blood pressure, and improves mood. "
                        "Even brief nature exposure enhances attention and cognitive function, a phenomenon sometimes called 'nature therapy'."
                    ),
                    "task": (
                        "Find a natural setting for this practice—a park, garden, forest, beach, or even a potted plant if outdoor spaces aren't accessible.\n\n"
                        "1. Begin with 3-5 minutes of mindful breathing to center yourself\n"
                        "2. Expand your awareness to sounds in nature—birds, wind, water, leaves\n"
                        "3. Notice visual details—colors, patterns, light, and shadow\n"
                        "4. Feel physical sensations—the temperature of air on your skin, the ground beneath you\n"
                        "5. If a particular aspect of nature draws your attention, focus on it fully:\n"
                        "   - If it's a tree, notice its unique characteristics\n"
                        "   - If it's a bird, observe its movements and sounds\n"
                        "   - If it's water, attend to its flow and rhythm\n"
                        "6. Before leaving, take a moment to express gratitude for this natural environment\n\n"
                        "Try to practice nature mindfulness for 15-20 minutes."
                    ),
                    "lesson": (
                        "Nature has a unique capacity to awaken our sense of wonder and presence. When we're in natural settings, "
                        "our attention often naturally becomes more receptive and open—qualities central to mindfulness.\n\n"
                        "In nature, we can experience a different sense of time—present-moment time rather than clock time. "
                        "Natural rhythms like sunrise and sunset, seasonal changes, and weather patterns remind us that we're "
                        "part of something larger than our individual concerns.\n\n"
                        "Connecting with nature mindfully can foster environmental awareness and stewardship. When we pay close "
                        "attention to the natural world, we often develop a deeper sense of care and responsibility for it."
                    )
                },
                {
                    "id": 15,
                    "theory": (
                        "Stress is an inevitable part of life, but mindfulness offers tools to work with stress more skillfully. "
                        "When we practice mindfulness during stressful situations, we learn to respond thoughtfully rather than react automatically.\n\n"
                        "The stress response evolved to help us deal with immediate physical threats, but today's stressors are often "
                        "chronic and psychological. Mindfulness helps break the cycle of stress reactivity by creating space between stimulus and response."
                    ),
                    "task": (
                        "Practice this STOP technique whenever you feel stressed today.\n\n"
                        "S - Stop what you're doing\n"
                        "T - Take a few deep breaths\n"
                        "O - Observe what's happening in your body, emotions, and thoughts\n"
                        "P - Proceed with awareness and intention\n\n"
                        "Extended practice (10-15 minutes):\n"
                        "1. Find a quiet space where you won't be disturbed\n"
                        "2. Sit comfortably and bring awareness to your breath\n"
                        "3. Scan your body for tension and breathe into those areas\n"
                        "4. Notice thoughts about stressors without following their stories\n"
                        "5. Remind yourself: 'This is a moment of stress, but I can respond wisely'\n"
                        "6. Ask yourself: 'What do I need right now?' and 'What matters most?'\n\n"
                        "Notice how creating space between the stressor and your response changes your experience of stress."
                    ),
                    "lesson": (
                        "The stress response is not inherently bad—it's designed to help us respond to threats. The problem arises "
                        "when we get stuck in chronic stress without recovery. Mindfulness helps activate the relaxation response, "
                        "allowing our systems to return to baseline.\n\n"
                        "We often cannot control external stressors, but we can influence how we relate to them. Mindfulness gives "
                        "us the ability to respond rather than react, making choices aligned with our values rather than driven by stress.\n\n"
                        "With practice, we can learn to recognize stress earlier, before it escalates. This early awareness creates "
                        "more options for responding skillfully and prevents stress from accumulating to overwhelming levels."
                    )
                },
                {
                    "id": 16,
                    "theory": (
                        "Communication forms the foundation of our relationships, yet we often speak and listen on autopilot. "
                        "Mindful communication involves bringing full awareness to how we express ourselves and how we receive others.\n\n"
                        "This practice helps us notice habitual patterns in our communication style and cultivates deeper, more authentic "
                        "connections. It involves being present with others rather than rehearsing what we'll say next or judging what's being said."
                    ),
                    "task": (
                        "Choose one conversation today to practice mindful communication.\n\n"
                        "When speaking:\n"
                        "1. Pause before responding\n"
                        "2. Consider your intention before speaking\n"
                        "3. Notice your tone of voice and body language\n"
                        "4. Speak truthfully but kindly\n\n"
                        "When listening:\n"
                        "1. Give your full attention to the speaker\n"
                        "2. Notice when your mind wanders and gently bring it back\n"
                        "3. Listen to understand rather than to respond\n"
                        "4. Notice any judgments that arise and let them go\n\n"
                        "After the conversation, reflect on how this mindful approach affected the quality of the interaction."
                    ),
                    "lesson": (
                        "Much of our communication happens on autopilot, driven by habit and unconscious patterns. Bringing mindfulness "
                        "to communication allows us to respond thoughtfully rather than reactively, enhancing the quality of our interactions.\n\n"
                        "Deep listening—being fully present for another without planning our response—is a profound gift we can offer "
                        "others. This quality of attention creates space for authentic connection and understanding.\n\n"
                        "Mindful communication isn't about perfect speech or constant awareness. It's about noticing when we've fallen "
                        "into unconscious patterns and gently returning to presence. Each interaction becomes an opportunity to practice."
                    )
                },
                {
                    "id": 17,
                    "theory": (
                        "Sleep difficulties often stem from an overactive mind or unprocessed stress from the day. Mindfulness "
                        "practices can create conditions conducive to healthy sleep by calming the nervous system and releasing tension.\n\n"
                        "When we bring awareness to the process of falling asleep, we learn to recognize and release thought patterns "
                        "that keep us awake. By grounding in bodily sensations, we help activate the parasympathetic nervous system."
                    ),
                    "task": (
                        "Practice this sequence as you prepare for sleep tonight.\n\n"
                        "1. Create a calm environment by reducing light and noise\n"
                        "2. Lie comfortably in bed and take 5-10 deep, slow breaths\n"
                        "3. Conduct a gentle body scan from toes to head, releasing tension with each exhale\n"
                        "4. If thoughts arise about tomorrow or today, note them briefly: 'planning' or 'remembering'\n"
                        "5. Return attention to physical sensations—the weight of your body on the bed, the rhythm of your breath\n"
                        "6. Notice the natural slowing of your breath as your body relaxes\n"
                        "7. If you find yourself awake and thinking, don't struggle—simply note 'thinking' and return to body sensations\n\n"
                        "If you wake during the night, use the same practice to help you return to sleep."
                    ),
                    "lesson": (
                        "Sleep is not something we can force—we can only create the conditions that allow sleep to arise naturally. "
                        "Mindfulness helps us let go of trying to sleep, which often paradoxically keeps us awake.\n\n"
                        "The transition from wakefulness to sleep provides a unique opportunity to observe how consciousness changes. "
                        "With practice, we can learn to recognize and enjoy the natural process of falling asleep rather than struggling with it.\n\n"
                        "Sleep and mindfulness share a common quality of letting go. Just as we practice letting go of thoughts during "
                        "meditation, we practice letting go of wakefulness as we fall asleep, trusting the natural wisdom of the body."
                    )
                },
                {
                    "id": 18,
                    "theory": (
                        "Mindful observation involves bringing detailed attention to an object or process. This practice develops "
                        "concentration and sensory clarity, fundamental skills for mindfulness.\n\n"
                        "When we observe mindfully, we suspend our normal categorizing mind and see with fresh eyes. This helps "
                        "counteract habituation—our tendency to stop noticing what's familiar—and awakens a sense of wonder in ordinary things."
                    ),
                    "task": (
                        "Choose an ordinary object for this mindful observation practice (10 minutes).\n\n"
                        "1. Select something you encounter regularly but rarely examine closely—a piece of fruit, a leaf, a stone, etc.\n"
                        "2. Hold the object in your hands or place it where you can observe it closely\n"
                        "3. Examine it as if seeing it for the first time or explaining it to someone who has never seen it\n"
                        "4. Notice:\n"
                        "   - Colors, patterns, textures, and shapes\n"
                        "   - How light interacts with the object\n"
                        "   - Any sounds it makes if you gently manipulate it\n"
                        "   - Its weight, temperature, and texture against your skin\n"
                        "   - Any smells or tastes (if it's a food item)\n"
                        "5. If your mind begins categorizing or storytelling, gently return to direct observation\n"
                        "6. Allow yourself to be curious and surprised by what you discover\n\n"
                        "After the practice, reflect: What did you notice that you hadn't before?"
                    ),
                    "lesson": (
                        "We often see what we expect to see rather than what's actually present. Mindful observation helps us "
                        "distinguish between direct perception and the concepts, labels, and stories we overlay on experience.\n\n"
                        "Even the most ordinary objects contain worlds of detail that we typically miss. This practice reveals the "
                        "extraordinary in the ordinary, awakening appreciation for the richness of sensory experience.\n\n"
                        "The quality of attention we bring to observation affects what we perceive. By developing the capacity for "
                        "sustained, curious attention, we expand our awareness of both outer and inner landscapes."
                    )
                },
                {
                    "id": 19,
                    "theory": (
                        "Mindful movement and stretching offer a way to practice mindfulness through the body. These practices help "
                        "bridge the perceived gap between mind and body by bringing awareness to physical sensations during movement.\n\n"
                        "Our bodies often reflect our mental states—tension, stress, and emotions manifest physically. By moving with "
                        "awareness, we can release physical tension and calm the mind simultaneously."
                    ),
                    "task": (
                        "Set aside 15-20 minutes for this mindful movement practice.\n\n"
                        "1. Begin standing with your feet hip-width apart\n"
                        "2. Close your eyes and take a few deep breaths, feeling your connection to the ground\n"
                        "3. Slowly raise your arms overhead while inhaling\n"
                        "4. Lower your arms while exhaling\n"
                        "5. Repeat this movement 5 times, focusing on the sensations\n"
                        "6. Gently bend to one side while inhaling, return to center while exhaling\n"
                        "7. Repeat on the other side, continuing for 5 rounds\n"
                        "8. Move through 5-10 minutes of gentle stretches, paying close attention to:  \n"
                        "   - The quality of each breath\n"
                        "   - Sensations of stretching and release\n"
                        "   - The subtle movements created by your breath\n"
                        "   - Areas of tension or ease\n\n"
                        "End by standing or sitting quietly for a minute, noticing how your body feels after this practice."
                    ),
                    "lesson": (
                        "Movement meditation can be especially beneficial for those who find seated meditation challenging. Some people "
                        "connect more easily with mindfulness through the body than through observing the breath or thoughts.\n\n"
                        "Mindful movement helps us recognize and release chronic tension patterns that we may hold unconsciously. "
                        "These patterns often reflect emotional states or habitual responses to stress.\n\n"
                        "The boundary between exercise and meditation dissolves when we bring full awareness to movement. Any physical "
                        "activity—walking, stretching, yoga, tai chi, swimming, dancing—can become meditation when approached mindfully."
                    )
                },
                {
                    "id": 20,
                    "theory": (
                        "Intention setting is the practice of consciously directing our attention and energy toward what matters most "
                        "to us. Unlike goals, which focus on future achievements, intentions guide our present moment experience.\n\n"
                        "By clarifying our intentions, we align our actions with our deepest values. This creates congruence between "
                        "our inner life and outer behavior, bringing a sense of authenticity and purpose to daily activities."
                    ),
                    "task": (
                        "Set aside 10-15 minutes for this intention-setting practice.\n\n"
                        "1. Find a quiet space and take several mindful breaths to center yourself\n"
                        "2. Reflect on these questions (you may want to journal your responses):\n"
                        "   - What matters most to me in this season of life?\n"
                        "   - How do I want to show up in my relationships and work?\n"
                        "   - What qualities do I want to cultivate (patience, courage, compassion, etc.)?\n"
                        "   - What would bring more meaning to my daily activities?\n"
                        "3. Based on your reflections, craft 1-3 simple intentions, stated in present tense:\n"
                        "   - 'I am cultivating patience with myself and others'\n"
                        "   - 'I am bringing full presence to conversations'\n"
                        "   - 'I am noticing moments of beauty in ordinary experiences'\n"
                        "4. Choose one primary intention for tomorrow\n"
                        "5. Identify specific situations where you can enact this intention\n"
                        "6. Consider creating a visual reminder or setting periodic alerts to reconnect with your intention\n\n"
                        "Tomorrow, notice when you're aligned with or diverging from your intention."
                    ),
                    "lesson": (
                        "Setting intentions is different from making plans or goals. While goals focus on achieving specific outcomes "
                        "in the future, intentions focus on how we want to be in the present moment, regardless of outcomes.\n\n"
                        "Our intentions act as an internal compass, helping us navigate daily choices and challenges. When faced with "
                        "a decision, we can ask: 'What choice best aligns with my deepest intentions?'\n\n"
                        "Regular intention setting integrates mindfulness into everyday life. By consciously choosing how we want to "
                        "show up in the world, we bring purpose and presence to ordinary activities."
                    )
                },
                {
                    "id": 21,
                    "theory": (
                        "Joy and wonder are natural states that arise when we're fully present. Mindfulness can help us notice and "
                        "cultivate these positive emotions that are often overlooked in our busy lives.\n\n"
                        "While our minds naturally focus on problems and threats, we can train ourselves to be more receptive to "
                        "positive experiences. This is not about denying difficulty but about maintaining a balanced awareness."
                    ),
                    "task": (
                        "Practice these joy and wonder exercises throughout the day:\n\n"
                        "1. Morning Intention (2 minutes):\n"
                        "   - Set an intention to notice moments of joy, beauty, or wonder\n"
                        "   - Create a simple phrase as a reminder: 'Open to joy' or 'Notice the good'\n\n"
                        "2. Joy Spotting (ongoing):\n"
                        "   - Throughout the day, pause to notice something positive\n"
                        "   - It might be as simple as the taste of food, a kind interaction, or a moment of ease\n"
                        "   - Take 15 seconds to fully absorb the experience\n\n"
                        "3. Wonder Walk (10-15 minutes):\n"
                        "   - Take a short walk with the specific intention of noticing what inspires wonder\n"
                        "   - Look up at the sky, notice plants growing through cracks, observe light and shadow\n"
                        "   - Approach your environment with childlike curiosity\n\n"
                        "4. Evening Reflection (5 minutes):\n"
                        "   - Write down three moments of joy or wonder from your day\n"
                        "   - For each one, note: What happened? How did it feel in your body? What conditions supported this experience?\n\n"
                        "Notice how intentionally cultivating positive states affects your overall sense of wellbeing."
                    ),
                    "lesson": (
                        "Joy and wonder are available in ordinary moments when we pay attention. These qualities don't require special "
                        "circumstances—they require presence and receptivity to what's already here.\n\n"
                        "The practice of savoring—fully feeling and extending positive experiences—counteracts our tendency to dismiss "
                        "good moments quickly while dwelling on negative ones. By lingering in moments of joy, we strengthen neural "
                        "pathways that support well-being.\n\n"
                        "Wonder arises when we drop our assumptions and see with fresh eyes. It reconnects us with the mystery and "
                        "miracle of ordinary existence, from the complexity of a flower to the vastness of the night sky."
                    )
                }
            ]
        }

    def save_content(self, content):
        """Save content to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(content, f, indent=4)

    def load_user_progress(self):
        """Load user progress from JSON file or create if not exists"""
        if os.path.exists(self.user_progress_file):
            try:
                with open(self.user_progress_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"completed_days": [], "reflections": {}}
        else:
            return {"completed_days": [], "reflections": {}}

    def save_user_progress(self):
        """Save user progress to JSON file"""
        with open(self.user_progress_file, 'w') as f:
            json.dump(self.completed_lessons, f, indent=4)

    def load_todays_content(self):
        """Load content for today based on date"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_id = hash(today) % len(self.content["daily_content"]) + 1
        
        # Find content for today
        for content in self.content["daily_content"]:
            if content["id"] == today_id:
                self.current_content = content
                break
        
        # Update UI with content
        self.update_content_display()
        
        # Update status bar
        completed_count = len(self.completed_lessons.get("completed_days", []))
        self.status_bar.config(text=f"Completed: {completed_count} days of mindfulness practice")
        
        # Check if today is already completed
        today_date = datetime.now().strftime("%Y-%m-%d")
        if today_date in self.completed_lessons.get("completed_days", []):
            self.complete_button.config(text="Today Completed", state="disabled")
        else:
            self.complete_button.config(text="Mark Today as Complete", state="normal")
        
        # Load today's reflection if exists
        if today_date in self.completed_lessons.get("reflections", {}):
            self.reflection_text.delete(1.0, tk.END)
            self.reflection_text.insert(tk.END, self.completed_lessons["reflections"][today_date])

    def load_random_content(self):
        """Load a random content item for preview"""
        # Exclude current content
        available_content = [c for c in self.content["daily_content"] 
                            if self.current_content is None or c["id"] != self.current_content["id"]]
        
        # Choose random content
        self.current_content = random.choice(available_content)
        
        # Update UI with content
        self.update_content_display()
        
        # Disable complete button for preview
        self.complete_button.config(text="Preview Mode (Cannot Complete)", state="disabled")
        
        # Clear reflection for preview
        self.reflection_text.delete(1.0, tk.END)
        
        # Update status bar
        self.status_bar.config(text="Preview Mode: This is a preview of another day's content")

    def update_content_display(self):
        """Update the UI with the current content"""
        if self.current_content:
            # Update theory text
            self.theory_text.configure(state="normal")
            self.theory_text.delete(1.0, tk.END)
            self.theory_text.insert(tk.END, self.current_content["theory"])
            self.theory_text.configure(state="disabled")
            
            # Update task text
            self.task_text.configure(state="normal")
            self.task_text.delete(1.0, tk.END)
            self.task_text.insert(tk.END, self.current_content["task"])
            self.task_text.configure(state="disabled")
            
            # Update lesson text
            self.lesson_text.configure(state="normal")
            self.lesson_text.delete(1.0, tk.END)
            self.lesson_text.insert(tk.END, self.current_content["lesson"])
            self.lesson_text.configure(state="disabled")

    def mark_as_complete(self):
        """Mark today's practice as complete"""
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        if today_date not in self.completed_lessons.get("completed_days", []):
            self.completed_lessons.setdefault("completed_days", []).append(today_date)
            self.save_user_progress()
            
            # Update UI to reflect completion
            self.complete_button.config(text="Today Completed", state="disabled")
            
            # Save current reflection
            self.save_reflection()
            
            # Show congratulation message
            messagebox.showinfo(
                "Day Completed", 
                "Congratulations on completing today's mindfulness practice!\n\n"
                "Remember that mindfulness is a journey, not a destination. "
                "Each day of practice builds your capacity for presence and awareness."
            )
            
            # Update status bar
            completed_count = len(self.completed_lessons.get("completed_days", []))
            self.status_bar.config(text=f"Completed: {completed_count} days of mindfulness practice")

    def save_reflection(self):
        """Save user's reflection for today"""
        today_date = datetime.now().strftime("%Y-%m-%d")
        reflection_text = self.reflection_text.get(1.0, tk.END).strip()
        
        if reflection_text:
            if "reflections" not in self.completed_lessons:
                self.completed_lessons["reflections"] = {}
                
            self.completed_lessons["reflections"][today_date] = reflection_text
            self.save_user_progress()
            
            # Show confirmation
            self.status_bar.config(text="Reflection saved successfully")
            
            # Reset status bar after 3 seconds
            self.root.after(3000, lambda: self.status_bar.config(
                text=f"Completed: {len(self.completed_lessons.get('completed_days', []))} days of mindfulness practice"
            ))

    def show_progress(self):
        """Show user progress in a new window"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Your Mindfulness Journey")
        progress_window.geometry("600x500")
        progress_window.configure(bg="#f5f5f7")
        
        # Title
        title_label = tk.Label(
            progress_window,
            text="Your Mindfulness Journey",
            font=("Helvetica", 18, "bold"),
            bg="#f5f5f7",
            fg="#333333"
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = tk.Label(
            progress_window,
            text="Track your progress and review past reflections",
            font=("Helvetica", 12),
            bg="#f5f5f7",
            fg="#666666"
        )
        desc_label.pack(pady=(0, 20))
        
        # Create scrollable frame for days
        main_frame = tk.Frame(progress_window, bg="#f5f5f7")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f7")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f7")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add streak info
        completed_days = self.completed_lessons.get("completed_days", [])
        streak = self.calculate_streak(completed_days)
        
        streak_frame = tk.Frame(scrollable_frame, bg="#f5f5f7", pady=10)
        streak_frame.pack(fill=tk.X)
        
        streak_label = tk.Label(
            streak_frame,
            text=f"Current Streak: {streak} days",
            font=("Helvetica", 14, "bold"),
            bg="#f5f5f7",
            fg="#333333"
        )
        streak_label.pack()
        
        total_label = tk.Label(
            streak_frame,
            text=f"Total Days Completed: {len(completed_days)}",
            font=("Helvetica", 12),
            bg="#f5f5f7",
            fg="#333333"
        )
        total_label.pack(pady=(5, 0))
        
        # Add calendar view
        calendar_label = tk.Label(
            scrollable_frame,
            text="Practice Calendar:",
            font=("Helvetica", 14, "bold"),
            bg="#f5f5f7",
            fg="#333333",
            anchor="w"
        )
        calendar_label.pack(fill=tk.X, pady=(20, 10))
        
        # Sort completed days
        sorted_days = sorted(completed_days, reverse=True)
        
        if sorted_days:
            for day in sorted_days:
                # Convert to datetime for formatting
                try:
                    date_obj = datetime.strptime(day, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%A, %B %d, %Y")
                except ValueError:
                    formatted_date = day  # Fallback if format is unexpected
                
                day_frame = tk.Frame(scrollable_frame, bg="#ffffff", padx=15, pady=12, bd=1, relief=tk.SOLID)
                day_frame.pack(fill=tk.X, pady=5)
                
                # Date label
                date_label = tk.Label(
                    day_frame,
                    text=formatted_date,
                    font=("Helvetica", 12, "bold"),
                    bg="#ffffff",
                    fg="#333333",
                    anchor="w"
                )
                date_label.pack(fill=tk.X)
                
                # Add view reflection button if reflection exists
                if day in self.completed_lessons.get("reflections", {}):
                    reflection_preview = self.completed_lessons["reflections"][day]
                    if len(reflection_preview) > 50:
                        reflection_preview = reflection_preview[:50] + "..."
                    
                    preview_label = tk.Label(
                        day_frame,
                        text=f"Reflection: {reflection_preview}",
                        font=("Helvetica", 10, "italic"),
                        bg="#ffffff",
                        fg="#666666",
                        anchor="w"
                    )
                    preview_label.pack(fill=tk.X, pady=(3, 5))
                    
                    # Create function to show reflection
                    def create_reflection_viewer(date, text):
                        return lambda: self.show_reflection(date, text)
                    
                    view_button = ttk.Button(
                        day_frame,
                        text="View Full Reflection",
                        command=create_reflection_viewer(
                            formatted_date, 
                            self.completed_lessons["reflections"][day]
                        )
                    )
                    view_button.pack(anchor="e")
        else:
            # No days completed message
            no_days_label = tk.Label(
                scrollable_frame,
                text="You haven't completed any mindfulness practice days yet.\nComplete today's practice to start your journey!",
                font=("Helvetica", 11),
                bg="#f5f5f7",
                fg="#666666"
            )
            no_days_label.pack(pady=20)
        
        # Stats frame
        stats_label = tk.Label(
            scrollable_frame,
            text="Your Practice Stats:",
            font=("Helvetica", 14, "bold"),
            bg="#f5f5f7",
            fg="#333333",
            anchor="w"
        )
        stats_label.pack(fill=tk.X, pady=(20, 10))
        
        stats_frame = tk.Frame(scrollable_frame, bg="#ffffff", padx=15, pady=15, bd=1, relief=tk.SOLID)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # Calculate some basic stats
        total_completed = len(completed_days)
        
        if completed_days:
            first_day = min(completed_days)
            try:
                first_date = datetime.strptime(first_day, "%Y-%m-%d")
                today = datetime.now()
                days_since_start = (today - first_date).days + 1
                completion_rate = round((total_completed / days_since_start) * 100, 1)
            except ValueError:
                days_since_start = 0
                completion_rate = 0
        else:
            days_since_start = 0
            completion_rate = 0
        
        # Add stats labels
        stats_day_label = tk.Label(
            stats_frame,
            text=f"Days practicing: {days_since_start}",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#333333",
            anchor="w"
        )
        stats_day_label.pack(fill=tk.X, pady=2)
        
        stats_completion_label = tk.Label(
            stats_frame,
            text=f"Completion rate: {completion_rate}%",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#333333",
            anchor="w"
        )
        stats_completion_label.pack(fill=tk.X, pady=2)
        
        stats_streak_label = tk.Label(
            stats_frame,
            text=f"Current streak: {streak} days",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#333333",
            anchor="w"
        )
        stats_streak_label.pack(fill=tk.X, pady=2)
        
        # Button to close window
        close_button = ttk.Button(
            progress_window,
            text="Close",
            command=progress_window.destroy
        )
        close_button.pack(pady=20)

    def show_reflection(self, date, text):
        """Show a full reflection in a new window"""
        reflection_window = tk.Toplevel(self.root)
        reflection_window.title(f"Reflection - {date}")
        reflection_window.geometry("500x400")
        reflection_window.configure(bg="#f5f5f7")
        
        # Title
        title_label = tk.Label(
            reflection_window,
            text=f"Your Reflection from {date}",
            font=("Helvetica", 16, "bold"),
            bg="#f5f5f7",
            fg="#333333"
        )
        title_label.pack(pady=(20, 10))
        
        # Reflection text
        reflection_frame = tk.Frame(reflection_window, bg="#f5f5f7", padx=20, pady=10)
        reflection_frame.pack(fill=tk.BOTH, expand=True)
        
        reflection_text = scrolledtext.ScrolledText(
            reflection_frame, 
            wrap=tk.WORD, 
            width=60, 
            height=15,
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#333333",
            padx=10,
            pady=10
        )
        reflection_text.pack(fill=tk.BOTH, expand=True)
        reflection_text.insert(tk.END, text)
        reflection_text.configure(state="disabled")
        
        # Close button
        close_button = ttk.Button(
            reflection_window,
            text="Close",
            command=reflection_window.destroy
        )
        close_button.pack(pady=15)

    def calculate_streak(self, completed_days):
        """Calculate the current streak of consecutive days"""
        if not completed_days:
            return 0
        
        # Convert strings to datetime objects
        try:
            date_objects = [datetime.strptime(day, "%Y-%m-%d") for day in completed_days]
        except ValueError:
            return 0
        
        # Sort dates in descending order (newest first)
        date_objects.sort(reverse=True)
        
        # Get today's date
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if today or yesterday is completed
        if date_objects[0].date() != today.date() and (today - date_objects[0]).days > 1:
            return 0  # Streak broken if last completion was before yesterday
        
        # Count consecutive days
        streak = 1
        for i in range(len(date_objects) - 1):
            if (date_objects[i] - date_objects[i+1]).days == 1:
                streak += 1
            else:
                break
                
        return streak


def main():
    """Main function to run the app"""
    root = tk.Tk()
    app = MindfulnessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
