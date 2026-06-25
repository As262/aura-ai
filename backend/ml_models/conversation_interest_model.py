"""
ML Model for Conversation Interest Analysis
Analyzes chat engagement, interest levels, and provides improvement suggestions
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Any
import re
import numpy as np
from collections import Counter
import json
import os

# Real-time local sentiment engine (pure-python, instant, no downloads)
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("[WARN] vaderSentiment not available. Install with: pip install vaderSentiment")


class ConversationInterestAnalyzer(nn.Module):
    """
    Neural network for analyzing conversation interest and engagement
    Features: response time, message length, emoji usage, question patterns
    """
    
    def __init__(self, input_size=75, hidden_size=256, output_size=5):
        super(ConversationInterestAnalyzer, self).__init__()
        
        # Enhanced network architecture - BIGGER AND BETTER
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size)
        self.dropout2 = nn.Dropout(0.25)
        
        self.fc3 = nn.Linear(hidden_size, hidden_size // 2)
        self.bn3 = nn.BatchNorm1d(hidden_size // 2)
        self.dropout3 = nn.Dropout(0.2)
        
        self.fc4 = nn.Linear(hidden_size // 2, output_size)
        
        # Interest level categories with percentage ranges
        self.interest_categories = [
            "Very Low (0-20%)",
            "Low (20-40%)", 
            "Moderate (40-60%)",
            "High (60-80%)",
            "Very High (80-100%)"
        ]
        
    def forward(self, x):
        """Enhanced forward pass through deeper network"""
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        x = F.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)
        
        x = self.fc4(x)
        return x


class ConversationAnalysisService:
    """
    Service for comprehensive conversation analysis
    """
    
    def __init__(self, model_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ConversationInterestAnalyzer().to(self.device)

        # Real-time sentiment engine (local, instant)
        self.sentiment = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None

        if model_path and os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
        
        # Enhanced engagement indicators
        self.positive_indicators = [
            'haha', 'lol', 'lmao', 'rofl', 'hehe', 'hihi', 
            '😂', '😊', '❤️', '🥰', '😍', '🤩', '✨', '🙌', '💕', '😁', '😄',
            'really', 'wow', 'amazing', 'awesome', 'cool', 'nice', 'great',
            'love', 'beautiful', 'perfect', 'fantastic', 'wonderful', 'incredible'
        ]
        
        self.negative_indicators = [
            'ok', 'k', 'hmm', 'idk', 'whatever', 'sure', 'fine', 'maybe',
            'meh', 'eh', 'nah', 'dunno', 'guess', 'suppose'
        ]
        
        # TEXT STYLE PATTERNS - ok vs okk vs okay vs okayyy
        self.text_style_patterns = {
            'enthusiasm': {
                'yesss': r'\b(yes{2,}|yess+)\b',
                'okayyy': r'\b(okay{2,}|okayy+)\b',
                'hiii': r'\b(hi{2,}|hii+|hey{2,})\b',
                'byeee': r'\b(bye{2,}|byee+)\b',
                'coool': r'\b(\w+(.)\2{2,})\b',  # Any repeated letters (coool, niceee)
            },
            'low_effort': {
                'ok': r'\b(ok|okay)\b$',  # Just "ok" or "okay" alone
                'k': r'\b(k|kk)\b$',  # Just "k"
                'hmm': r'\b(hm+|hmm+)\b$',
                'mhm': r'\b(mhm+|mhmm+)\b$',
                'yeah': r'\b(yeah|yea|yah)\b$',
            },
            'variations': {
                'haha_short': r'\b(ha|hah)\b',  # Low effort laugh
                'haha_medium': r'\b(haha|hehe)\b',  # Medium laugh
                'haha_long': r'\b(haha{2,}|hehe{2,}|lol+)\b',  # High enthusiasm laugh
            }
        }
        
        # EMOJI PATTERNS AND MEANINGS
        self.emoji_categories = {
            'high_interest': ['😍', '🥰', '😘', '❤️', '💕', '💖', '💗', '💓', '💝', '🤩', '✨'],
            'happy': ['😊', '😄', '😁', '😃', '😀', '🙂', '☺️', '😌'],
            'laughing': ['😂', '🤣', '😹', '💀'],
            'excited': ['🤗', '🙌', '👏', '🎉', '🎊', '🥳'],
            'thinking': ['🤔', '💭', '🧐'],
            'neutral': ['😐', '😑', '😶', '🙄'],
            'sad': ['😢', '😭', '😞', '😔', '☹️', '😕'],
            'fire': ['🔥', '💯'],
            'cool': ['😎', '🆒'],
        }
        
        self.question_patterns = [
            r'\?$',  # Ends with ?
            r'^(what|when|where|why|how|who|which)',  # Question words
            r'^(do|does|did|can|could|would|should|will)',  # Auxiliary verbs
            r'(what|when|where|why|how|who|which)',  # Question words anywhere
        ]
    
    def extract_features(self, your_message: str, their_response: str) -> np.ndarray:
        """
        Extract ENHANCED features from message pair for ML analysis
        
        Returns 75-dimensional feature vector with advanced text style and emoji analysis
        """
        features = []
        
        # 1. Message length features (4 features)
        your_len = len(your_message.split())
        their_len = len(their_response.split())
        features.extend([
            your_len,
            their_len,
            their_len / max(your_len, 1),  # Response length ratio
            len(their_response)  # Character count
        ])
        
        # 2. Emoji and emoticon features (6 features)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        your_emojis = len(emoji_pattern.findall(your_message))
        their_emojis = len(emoji_pattern.findall(their_response))
        
        features.extend([
            your_emojis,
            their_emojis,
            1 if their_emojis > 0 else 0,  # Has emoji
            their_emojis / max(their_len, 1),  # Emoji density
            their_response.count('!'),  # Exclamation marks
            their_response.count('?')  # Question marks
        ])
        
        # 3. Engagement indicators (8 features)
        their_lower = their_response.lower()
        positive_count = sum(1 for indicator in self.positive_indicators if indicator in their_lower)
        negative_count = sum(1 for indicator in self.negative_indicators if indicator in their_lower)
        
        features.extend([
            positive_count,
            negative_count,
            1 if positive_count > 0 else 0,
            1 if negative_count > 0 else 0,
            their_response.count('haha'),
            their_response.count('lol'),
            their_response.count('lmao'),
            1 if any(emoji in their_response for emoji in ['😂', '😊', '❤️']) else 0
        ])
        
        # 4. Question and conversation flow (8 features)
        your_has_question = 1 if '?' in your_message else 0
        their_has_question = 1 if '?' in their_response else 0
        
        your_question_type = sum(1 for pattern in self.question_patterns 
                                 if re.search(pattern, your_message.lower()))
        their_question_type = sum(1 for pattern in self.question_patterns 
                                  if re.search(pattern, their_response.lower()))
        
        features.extend([
            your_has_question,
            their_has_question,
            your_question_type,
            their_question_type,
            1 if their_has_question and not your_has_question else 0,  # Asking back
            len(their_response.split('.')),  # Number of sentences
            1 if their_len > your_len else 0,  # Longer response
            1 if their_response.isupper() else 0  # All caps (excitement)
        ])
        
        # 5. Linguistic features (10 features)
        # Repetition and emphasis
        words_their = their_response.lower().split()
        word_freq = Counter(words_their)
        most_common_count = word_freq.most_common(1)[0][1] if word_freq else 0
        
        features.extend([
            most_common_count,  # Most repeated word count
            len(set(words_their)) / max(len(words_their), 1),  # Vocabulary diversity
            their_response.count('...'),  # Ellipsis usage
            their_response.count(','),  # Comma usage
            1 if their_response[0].isupper() else 0,  # Starts with capital
            sum(1 for char in their_response if char.isupper()) / max(len(their_response), 1),  # Capital ratio
            their_response.count('"'),  # Quote usage
            their_response.count("'"),  # Apostrophe usage
            1 if re.search(r'\b(my|me|i|mine)\b', their_lower) else 0,  # Self-reference
            1 if re.search(r'\b(you|your|yours)\b', their_lower) else 0  # You-reference
        ])
        
        # 6. Timing and pattern features (8 features) - placeholder for now
        # In real implementation, these would come from message timestamps
        features.extend([
            0.5,  # Response speed (normalized)
            0.7,  # Conversation continuity
            0.6,  # Topic maintenance
            0.8,  # Engagement consistency
            1,    # Is daytime
            0,    # Is late night
            0.5,  # Conversation position (start/middle/end)
            0.3   # Time since last message
        ])
        
        # 7. Additional semantic features (6 features)
        features.extend([
            1 if re.search(r'\b(love|like|enjoy|fun|happy)\b', their_lower) else 0,  # Positive emotion
            1 if re.search(r'\b(hate|dislike|boring|tired|sad)\b', their_lower) else 0,  # Negative emotion
            1 if re.search(r'\b(we|us|our)\b', their_lower) else 0,  # Inclusive language
            1 if re.search(r'\b(maybe|perhaps|possibly|might)\b', their_lower) else 0,  # Uncertainty
            1 if re.search(r'\b(definitely|absolutely|certainly|sure)\b', their_lower) else 0,  # Certainty
            1 if len(their_response.strip()) < 3 else 0  # Very short response
        ])
        
        # 8. TEXT STYLE ANALYSIS - ok vs okk vs okay vs okayyy (10 features)
        their_lower = their_response.lower()
        
        # Enthusiasm patterns (repeated letters show excitement)
        enthusiasm_score = 0
        for pattern_name, pattern in self.text_style_patterns['enthusiasm'].items():
            if re.search(pattern, their_lower):
                enthusiasm_score += 1
        
        # Low effort patterns (single word responses)
        low_effort_score = 0
        for pattern_name, pattern in self.text_style_patterns['low_effort'].items():
            if re.search(pattern, their_lower):
                low_effort_score += 1
        
        # Laugh variations (haha vs hahaha vs lol)
        laugh_score = 0
        if re.search(self.text_style_patterns['variations']['haha_long'], their_lower):
            laugh_score = 3  # High enthusiasm
        elif re.search(self.text_style_patterns['variations']['haha_medium'], their_lower):
            laugh_score = 2  # Medium
        elif re.search(self.text_style_patterns['variations']['haha_short'], their_lower):
            laugh_score = 1  # Low
        
        # Check for letter repetition patterns (coool, niceee, etc.)
        letter_repetition = len(re.findall(r'(.)\1{2,}', their_response))  # 3+ repeated chars
        
        features.extend([
            enthusiasm_score,  # How many enthusiasm patterns found
            low_effort_score,  # How many low-effort patterns found
            laugh_score,  # Quality of laugh (0-3)
            letter_repetition,  # Number of repeated letter instances
            1 if enthusiasm_score > 0 else 0,  # Has any enthusiasm
            1 if low_effort_score > 0 else 0,  # Has any low-effort
            1 if 'okayyy' in their_lower or 'okayy' in their_lower else 0,  # Extended okay
            1 if their_lower.strip() in ['ok', 'k', 'okay'] else 0,  # Just ok/k/okay
            1 if 'yesss' in their_lower or 'yess' in their_lower else 0,  # Extended yes
            1 if 'hiii' in their_lower or 'heyy' in their_lower else 0,  # Extended greeting
        ])
        
        # 9. EMOJI PATTERN ANALYSIS (10 features)
        # Count emojis by category
        high_interest_emojis = sum(1 for emoji in self.emoji_categories['high_interest'] if emoji in their_response)
        happy_emojis = sum(1 for emoji in self.emoji_categories['happy'] if emoji in their_response)
        laughing_emojis = sum(1 for emoji in self.emoji_categories['laughing'] if emoji in their_response)
        excited_emojis = sum(1 for emoji in self.emoji_categories['excited'] if emoji in their_response)
        thinking_emojis = sum(1 for emoji in self.emoji_categories['thinking'] if emoji in their_response)
        neutral_emojis = sum(1 for emoji in self.emoji_categories['neutral'] if emoji in their_response)
        sad_emojis = sum(1 for emoji in self.emoji_categories['sad'] if emoji in their_response)
        fire_emojis = sum(1 for emoji in self.emoji_categories['fire'] if emoji in their_response)
        
        # Emoji diversity score
        emoji_types_used = sum([
            1 if high_interest_emojis > 0 else 0,
            1 if happy_emojis > 0 else 0,
            1 if laughing_emojis > 0 else 0,
            1 if excited_emojis > 0 else 0,
        ])
        
        features.extend([
            high_interest_emojis,  # Love and heart emojis
            happy_emojis,  # Smiling emojis
            laughing_emojis,  # Laughing emojis
            excited_emojis,  # Excited/celebrating emojis
            thinking_emojis,  # Thinking emojis (moderate interest)
            neutral_emojis,  # Neutral face emojis (low interest)
            sad_emojis,  # Sad emojis (negative)
            fire_emojis,  # Fire/100 emojis (high interest)
            emoji_types_used,  # Diversity of emoji types
            1 if (high_interest_emojis + laughing_emojis + excited_emojis) > 2 else 0  # Multiple positive emojis
        ])
        
        # 10. ADVANCED ENGAGEMENT METRICS (5 features)
        # Punctuation enthusiasm
        exclamation_count = their_response.count('!')
        multiple_exclamations = 1 if '!!' in their_response or '!!!' in their_response else 0
        multiple_questions = 1 if '??' in their_response or '???' in their_response else 0
        
        # Capital letters for emphasis
        caps_words = sum(1 for word in their_response.split() if word.isupper() and len(word) > 1)
        
        # Message enthusiasm score (combined metric)
        enthusiasm_total = (
            exclamation_count * 0.5 +
            multiple_exclamations * 2 +
            caps_words * 1.5 +
            letter_repetition * 1 +
            enthusiasm_score * 2
        )
        
        features.extend([
            exclamation_count,  # Number of !
            multiple_exclamations,  # !! or !!!
            multiple_questions,  # ?? or ???
            caps_words,  # Number of ALL CAPS words
            min(enthusiasm_total, 10) / 10  # Normalized total enthusiasm (0-1)
        ])
        
        # Ensure we have exactly 75 features
        while len(features) < 75:
            features.append(0.0)
        
        return np.array(features[:75], dtype=np.float32)
    
    def analyze_conversation(self, messages: List[Dict], user_identifier: str = None) -> Dict[str, Any]:
        """
        Comprehensive conversation analysis
        
        Args:
            messages: List of message dicts with 'sender' and 'message'
            user_identifier: Identifier for the user (to separate their messages)
            
        Returns:
            Detailed analysis with interest levels and suggestions
        """
        if len(messages) < 2:
            return {
                'error': 'Not enough messages for analysis',
                'minimum_required': 2
            }
        
        # Identify participants
        senders = {}
        for msg in messages:
            sender = msg['sender']
            senders[sender] = senders.get(sender, 0) + 1
        
        # Get top 2 participants
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if len(top_senders) < 2:
            return {
                'error': 'Need at least 2 participants',
                'participants_found': len(top_senders)
            }
        
        # Determine who is "you" and who is "them"
        if user_identifier:
            user = user_identifier
            other = next((s for s, _ in top_senders if s != user), top_senders[0][0])
        else:
            # Assume first participant is "you"
            user = top_senders[0][0]
            other = top_senders[1][0]
        
        # Extract conversation pairs and analyze
        your_messages = [msg for msg in messages if msg['sender'] == user]
        their_messages = [msg for msg in messages if msg['sender'] == other]
        
        # Get response pairs
        pairs = []
        for i in range(len(messages) - 1):
            if messages[i]['sender'] == user and messages[i + 1]['sender'] == other:
                pairs.append((messages[i]['message'], messages[i + 1]['message']))
        
        if not pairs:
            return {
                'error': 'No conversation pairs found',
                'your_messages': len(your_messages),
                'their_messages': len(their_messages)
            }
        
        # Analyze each pair
        interest_scores = []
        detailed_pairs = []
        
        # Set model to evaluation mode for inference
        self.model.eval()
        
        for your_msg, their_msg in pairs:
            features = self.extract_features(your_msg, their_msg)
            
            # Run through model
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
                output = self.model(features_tensor)
                probabilities = F.softmax(output, dim=1)
                interest_level = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][interest_level].item()
            
            interest_scores.append(interest_level)
            detailed_pairs.append({
                'your_message': your_msg[:100] + '...' if len(your_msg) > 100 else your_msg,
                'their_response': their_msg[:100] + '...' if len(their_msg) > 100 else their_msg,
                'interest_level': self.model.interest_categories[interest_level],
                'confidence': round(confidence * 100, 2)
            })
        
        # Calculate overall statistics with PERCENTAGE BREAKDOWN
        avg_interest = np.mean(interest_scores)
        interest_distribution = Counter(interest_scores)

        # Trained-model percentage score (0-100%)
        model_percentage = (avg_interest / 4) * 100

        # ---- Real-time sentiment layer (VADER, local) ----
        sentiment_analysis = self._analyze_sentiment(their_messages, pairs)
        sentiment_pct = sentiment_analysis['engagement_percentage']

        # Blend the trained model with live sentiment for the final interest read.
        # Model captures structural engagement; sentiment captures live tone.
        if sentiment_analysis.get('available'):
            interest_percentage = round(model_percentage * 0.55 + sentiment_pct * 0.45, 1)
        else:
            interest_percentage = round(model_percentage, 1)

        # Detailed percentage breakdown
        percentage_breakdown = {
            'overall_interest': round(interest_percentage, 1),
            'their_engagement_score': round(sentiment_pct, 1),
            'model_interest_score': round(model_percentage, 1),
            'conversation_quality': round(min(interest_percentage * 1.05, 100), 1),
            'compatibility_score': round(interest_percentage * 0.95, 1),
        }
        
        # Confidence metrics
        confidence_scores = []
        for i, score in enumerate(interest_scores):
            if i < len(detailed_pairs):
                confidence_scores.append(detailed_pairs[i]['confidence'])
        
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        
        # Generate improvement suggestions (now sentiment-aware)
        suggestions = self._generate_suggestions(pairs, interest_scores, your_messages, their_messages, sentiment_analysis)
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(
            your_messages, their_messages, pairs
        )
        
        # Add text style analysis summary
        text_style_summary = self._analyze_text_styles(their_messages)
        
        # Add emoji usage summary
        emoji_summary = self._analyze_emoji_patterns(their_messages)
        
        # Interest level interpretation
        if interest_percentage >= 80:
            interest_interpretation = "🔥 VERY HIGH INTEREST! They're clearly very engaged and interested in you!"
        elif interest_percentage >= 60:
            interest_interpretation = "😊 HIGH INTEREST! The conversation is going great!"
        elif interest_percentage >= 40:
            interest_interpretation = "🤔 MODERATE INTEREST. There's potential, keep building connection!"
        elif interest_percentage >= 20:
            interest_interpretation = "😐 LOW INTEREST. Try to engage more or find common interests."
        else:
            interest_interpretation = "⚠️ VERY LOW INTEREST. They might not be very engaged right now."
        
        return {
            # Main Results
            'overall_interest_level': self.model.interest_categories[int(round(avg_interest))],
            'interest_percentage': round(interest_percentage, 1),
            'interest_interpretation': interest_interpretation,
            
            # Detailed Percentage Breakdown
            'percentage_breakdown': percentage_breakdown,
            'average_interest_score': round(avg_interest, 2),
            'confidence_level': round(avg_confidence, 1),
            
            # Distribution
            'interest_distribution': {
                self.model.interest_categories[i]: interest_distribution.get(i, 0)
                for i in range(5)
            },
            'distribution_percentages': {
                self.model.interest_categories[i]: round((interest_distribution.get(i, 0) / len(pairs)) * 100, 1)
                for i in range(5)
            },
            
            # Message Stats
            'total_messages': len(messages),
            'your_messages': len(your_messages),
            'their_messages': len(their_messages),
            'conversation_pairs_analyzed': len(pairs),
            
            # Advanced Analysis
            'engagement_metrics': engagement_metrics,
            'sentiment_analysis': sentiment_analysis,
            'text_style_analysis': text_style_summary,
            'emoji_analysis': emoji_summary,
            
            # Detailed Results
            'detailed_pair_analysis': detailed_pairs[:10],  # First 10 pairs
            'improvement_suggestions': suggestions,
            
            # Participants
            'participants': {
                'you': user,
                'other_person': other
            }
        }
    
    def _analyze_text_styles(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze text style patterns (ok vs okk vs okay vs okayyy)"""
        
        enthusiasm_count = 0
        low_effort_count = 0
        laugh_patterns = {'short': 0, 'medium': 0, 'long': 0}
        repeated_letters = 0
        
        for msg in messages:
            text = msg['message'].lower()
            
            # Check enthusiasm patterns
            for pattern in self.text_style_patterns['enthusiasm'].values():
                if re.search(pattern, text):
                    enthusiasm_count += 1
            
            # Check low-effort patterns
            for pattern in self.text_style_patterns['low_effort'].values():
                if re.search(pattern, text):
                    low_effort_count += 1
            
            # Check laugh patterns
            if re.search(self.text_style_patterns['variations']['haha_long'], text):
                laugh_patterns['long'] += 1
            elif re.search(self.text_style_patterns['variations']['haha_medium'], text):
                laugh_patterns['medium'] += 1
            elif re.search(self.text_style_patterns['variations']['haha_short'], text):
                laugh_patterns['short'] += 1
            
            # Count repeated letters
            repeated_letters += len(re.findall(r'(.)\1{2,}', text))
        
        total_messages = len(messages)
        
        return {
            'enthusiasm_patterns': enthusiasm_count,
            'enthusiasm_percentage': round((enthusiasm_count / max(total_messages, 1)) * 100, 1),
            'low_effort_responses': low_effort_count,
            'low_effort_percentage': round((low_effort_count / max(total_messages, 1)) * 100, 1),
            'laugh_quality': {
                'high_enthusiasm': laugh_patterns['long'],
                'medium_enthusiasm': laugh_patterns['medium'],
                'low_enthusiasm': laugh_patterns['short']
            },
            'letter_repetition_count': repeated_letters,
            'style_score': round(max(0, (enthusiasm_count - low_effort_count * 2) / max(total_messages, 1) * 100), 1),
            'interpretation': self._interpret_text_style(enthusiasm_count, low_effort_count, total_messages)
        }
    
    def _interpret_text_style(self, enthusiasm: int, low_effort: int, total: int) -> str:
        """Interpret text style patterns"""
        enthusiasm_ratio = enthusiasm / max(total, 1)
        low_effort_ratio = low_effort / max(total, 1)
        
        if enthusiasm_ratio > 0.4:
            return "🔥 Very enthusiastic texter! Lots of energy and excitement!"
        elif enthusiasm_ratio > 0.2:
            return "😊 Engaged texter with good energy"
        elif low_effort_ratio > 0.4:
            return "😐 Mostly low-effort responses (ok, k, hmm)"
        elif low_effort_ratio > 0.2:
            return "🤔 Mixed effort, some low-effort responses"
        else:
            return "👍 Balanced texting style"
    
    def _analyze_emoji_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze emoji usage patterns"""
        
        emoji_counts = {category: 0 for category in self.emoji_categories.keys()}
        total_emojis = 0
        messages_with_emojis = 0
        
        for msg in messages:
            text = msg['message']
            has_emoji = False
            
            for category, emoji_list in self.emoji_categories.items():
                count = sum(1 for emoji in emoji_list if emoji in text)
                emoji_counts[category] += count
                total_emojis += count
                if count > 0:
                    has_emoji = True
            
            if has_emoji:
                messages_with_emojis += 1
        
        total_messages = len(messages)
        emoji_usage_rate = (messages_with_emojis / max(total_messages, 1)) * 100
        
        # Calculate positive emoji percentage
        positive_emojis = (emoji_counts['high_interest'] + emoji_counts['happy'] + 
                          emoji_counts['laughing'] + emoji_counts['excited'])
        positive_percentage = (positive_emojis / max(total_emojis, 1)) * 100
        
        return {
            'total_emojis': total_emojis,
            'emoji_usage_rate': round(emoji_usage_rate, 1),
            'emojis_per_message': round(total_emojis / max(total_messages, 1), 2),
            'messages_with_emojis': messages_with_emojis,
            'emoji_categories': {
                'high_interest': emoji_counts['high_interest'],
                'happy': emoji_counts['happy'],
                'laughing': emoji_counts['laughing'],
                'excited': emoji_counts['excited'],
                'thinking': emoji_counts['thinking'],
                'neutral': emoji_counts['neutral'],
                'sad': emoji_counts['sad'],
                'fire': emoji_counts['fire'],
            },
            'positive_emoji_percentage': round(positive_percentage, 1),
            'interpretation': self._interpret_emoji_usage(emoji_usage_rate, positive_percentage, emoji_counts)
        }
    
    def _interpret_emoji_usage(self, usage_rate: float, positive_pct: float, counts: Dict) -> str:
        """Interpret emoji usage patterns"""
        if usage_rate > 70 and positive_pct > 70:
            return "🥰 Extremely expressive! Lots of positive emojis - great sign!"
        elif usage_rate > 50 and positive_pct > 60:
            return "😊 Good emoji usage with positive vibes!"
        elif usage_rate > 30:
            return "🙂 Moderate emoji user"
        elif usage_rate > 10:
            return "😐 Light emoji usage"
        else:
            return "📝 Minimal emoji usage - prefers plain text"
    
    def _calculate_engagement_metrics(self, your_messages: List[Dict], 
                                     their_messages: List[Dict],
                                     pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Calculate detailed engagement metrics"""
        
        # Message length analysis
        your_avg_length = np.mean([len(msg['message'].split()) for msg in your_messages])
        their_avg_length = np.mean([len(msg['message'].split()) for msg in their_messages])
        
        # Response ratio
        response_ratio = their_avg_length / max(your_avg_length, 1)
        
        # Question asking
        your_questions = sum(1 for msg in your_messages if '?' in msg['message'])
        their_questions = sum(1 for msg in their_messages if '?' in msg['message'])
        
        # Emoji usage
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        your_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in your_messages)
        their_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in their_messages)
        
        # Positive indicators
        their_positive = sum(
            sum(1 for indicator in self.positive_indicators 
                if indicator in msg['message'].lower())
            for msg in their_messages
        )
        
        return {
            'your_avg_message_length': round(your_avg_length, 2),
            'their_avg_message_length': round(their_avg_length, 2),
            'response_length_ratio': round(response_ratio, 2),
            'your_questions_asked': your_questions,
            'their_questions_asked': their_questions,
            'question_reciprocation_rate': round(their_questions / max(your_questions, 1), 2),
            'your_emoji_usage': your_emojis,
            'their_emoji_usage': their_emojis,
            'their_positive_reactions': their_positive,
            'engagement_balance': round(min(response_ratio, 1/response_ratio), 2)  # Closer to 1 is better
        }
    
    def _generate_suggestions(self, pairs: List[Tuple[str, str]],
                            interest_scores: List[int],
                            your_messages: List[Dict],
                            their_messages: List[Dict],
                            sentiment_analysis: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        Generate DYNAMIC, AI-powered improvement suggestions based on actual conversation analysis
        Analyzes real message content, patterns, and context to provide personalized tips
        """

        all_suggestions = []

        # === REAL-TIME SENTIMENT-DRIVEN ADVICE (VADER) ===
        if sentiment_analysis and sentiment_analysis.get('available'):
            trajectory = sentiment_analysis.get('trajectory')
            positivity = sentiment_analysis.get('positivity', 0)
            negativity = sentiment_analysis.get('negativity', 0)

            # Surface the message that landed best to double down on what works
            best_pair, best_compound = None, -2.0
            for your_msg, their_msg in pairs:
                c = self._sentiment_compound(their_msg)
                if c > best_compound:
                    best_compound, best_pair = c, (your_msg, their_msg)

            if trajectory == 'cooling off':
                all_suggestions.append({
                    'category': 'Sentiment Cooling',
                    'priority': 'High',
                    'suggestion': f"Their tone has cooled by {abs(sentiment_analysis.get('trajectory_delta', 0)):.0f} points over the chat. The positive energy from earlier is fading.",
                    'tip': 'Re-introduce a topic that worked earlier, or switch to something playful and open-ended to rekindle the spark.'
                })
            elif trajectory == 'warming up':
                all_suggestions.append({
                    'category': 'Sentiment Warming',
                    'priority': 'Info',
                    'suggestion': f"Their sentiment is trending up (+{sentiment_analysis.get('trajectory_delta', 0):.0f} points). You're building real momentum.",
                    'tip': 'Keep leaning into the current thread - it is clearly landing well.'
                })

            if negativity > 25:
                all_suggestions.append({
                    'category': 'Negative Tone Detected',
                    'priority': 'High',
                    'suggestion': f"About {negativity:.0f}% of their replies carry a negative tone. Something may be creating friction.",
                    'tip': 'Acknowledge their feelings, ease the pressure, and avoid loaded or one-word-answer questions.'
                })
            elif positivity > 60 and best_pair:
                preview = best_pair[0][:55] + ('...' if len(best_pair[0]) > 55 else '')
                all_suggestions.append({
                    'category': 'What Is Working',
                    'priority': 'Info',
                    'suggestion': f"Their most positive reaction came after you said: \"{preview}\". That direction resonates.",
                    'tip': 'Explore more of that theme - ask follow-up questions around what sparked the positive response.'
                })

        # === DYNAMIC ANALYSIS OF ACTUAL CONVERSATION CONTENT ===
        
        # 1. Analyze low interest pairs with SPECIFIC examples
        low_interest_pairs = [(pairs[i], interest_scores[i]) for i, score in enumerate(interest_scores) if score <= 1]
        
        if len(low_interest_pairs) > len(pairs) * 0.4:
            # Find the ACTUAL worst performing message
            worst_pair = min(low_interest_pairs, key=lambda x: x[1]) if low_interest_pairs else None
            if worst_pair:
                your_msg_preview = worst_pair[0][0][:50] + "..." if len(worst_pair[0][0]) > 50 else worst_pair[0][0]
                their_response = worst_pair[0][1][:50] + "..." if len(worst_pair[0][1]) > 50 else worst_pair[0][1]
                
                all_suggestions.append({
                    'category': 'Low Response Quality',
                    'priority': 'High',
                    'suggestion': f'When you said "{your_msg_preview}", they responded with "{their_response}" which shows low engagement. Try asking more open-ended questions that invite detailed responses.',
                    'tip': f'Instead of short statements, try: "Tell me more about..." or "What was your favorite part of..."'
                })
        
        # 2. DYNAMIC Message length analysis with ACTUAL examples
        your_lengths = [len(msg['message'].split()) for msg in your_messages]
        their_lengths = [len(msg['message'].split()) for msg in their_messages]
        your_avg = np.mean(your_lengths)
        their_avg = np.mean(their_lengths)
        
        if your_avg > their_avg * 2:
            # Find longest message as example
            longest_idx = your_lengths.index(max(your_lengths))
            long_msg = your_messages[longest_idx]['message']
            preview = long_msg[:80] + "..." if len(long_msg) > 80 else long_msg
            
            all_suggestions.append({
                'category': 'Message Balance',
                'priority': 'Medium',
                'suggestion': f'Your messages average {your_avg:.1f} words while theirs average {their_avg:.1f}. For example: "{preview}" - This might overwhelm them. Try breaking thoughts into smaller chunks.',
                'tip': f'Split long messages into 2-3 shorter ones and ask questions between them to invite their input.'
            })
        elif your_avg < their_avg * 0.5:
            # Find shortest message as example
            shortest_idx = your_lengths.index(min(your_lengths))
            short_msg = your_messages[shortest_idx]['message']
            
            all_suggestions.append({
                'category': 'Message Depth',
                'priority': 'Medium',
                'suggestion': f'Your messages average {your_avg:.1f} words while theirs average {their_avg:.1f}. Messages like "{short_msg}" feel too brief. Show more investment by elaborating on your thoughts.',
                'tip': f'Add context, personal feelings, or follow-up questions. Instead of "{short_msg}", explain WHY you feel that way.'
            })
        
        # 3. DYNAMIC Question analysis with SPECIFIC conversation context
        your_question_msgs = [msg for msg in your_messages if '?' in msg['message']]
        their_question_msgs = [msg for msg in their_messages if '?' in msg['message']]
        your_questions = len(your_question_msgs)
        their_questions = len(their_question_msgs)
        
        if your_questions < len(your_messages) * 0.2:
            # Analyze what topics they're interested in based on their longest responses
            interested_topics = []
            for i, (your_msg, their_msg) in enumerate(pairs):
                if len(their_msg.split()) > their_avg * 1.3:  # They elaborated here
                    # Extract key words from your message that triggered interest
                    words = [w.lower() for w in your_msg.split() if len(w) > 4 and w.isalpha()]
                    interested_topics.extend(words[:2])  # Take first 2 meaningful words
            
            topic_hint = f" about {interested_topics[0]}" if interested_topics else ""
            
            all_suggestions.append({
                'category': 'Conversation Depth',
                'priority': 'High',
                'suggestion': f'You asked only {your_questions} questions in {len(your_messages)} messages ({your_questions/len(your_messages)*100:.0f}%). They seem engaged when you talk{topic_hint}. Ask more questions to deepen the connection!',
                'tip': f'Try: "What do you think about...?", "How did that make you feel?", or "Tell me more about..." to invite detailed responses.'
            })
        
        if their_questions < len(their_messages) * 0.15:
            # Find messages where YOU elaborated but they didn't ask follow-ups
            missed_opportunities = []
            for msg in your_messages:
                if len(msg['message'].split()) > your_avg * 1.5:
                    preview = msg['message'][:60] + "..." if len(msg['message']) > 60 else msg['message']
                    missed_opportunities.append(preview)
            
            example = missed_opportunities[0] if missed_opportunities else "your detailed stories"
            
            all_suggestions.append({
                'category': 'Reciprocal Interest',
                'priority': 'Medium',
                'suggestion': f'They only asked {their_questions} questions back. When you shared: "{example}", they didn\'t ask follow-ups. Make your stories more intriguing to spark curiosity.',
                'tip': f'End statements with hooks like: "...and you won\'t believe what happened next!" or "...have you ever experienced something like that?"'
            })
        
        # 4. DYNAMIC Emoji analysis with ACTUAL emoji patterns
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        your_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in your_messages)
        their_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in their_messages)
        
        # Analyze WHICH emojis they use
        their_emoji_examples = []
        for msg in their_messages[:5]:  # Check first 5 messages
            found_emojis = emoji_pattern.findall(msg['message'])
            their_emoji_examples.extend(found_emojis)
        
        if your_emojis < len(your_messages) * 0.3 and their_emojis > len(their_messages) * 0.5:
            emoji_sample = ''.join(their_emoji_examples[:5]) if their_emoji_examples else '😊😂❤️'
            
            all_suggestions.append({
                'category': 'Communication Style Match',
                'priority': 'Medium',
                'suggestion': f'They use {their_emojis} emojis (like {emoji_sample}) but you only use {your_emojis}. They express emotions through emojis - match their style to connect better!',
                'tip': f'Start using emojis like {emoji_sample} in your messages to match their expressive communication style.'
            })
        
        # 5. DYNAMIC Positive language analysis with SPECIFIC examples
        their_positive_msgs = []
        positive_indicators_found = []
        
        for msg in their_messages:
            msg_lower = msg['message'].lower()
            for indicator in self.positive_indicators:
                if indicator in msg_lower:
                    their_positive_msgs.append(msg['message'][:50])
                    positive_indicators_found.append(indicator)
        
        if len(their_positive_msgs) > len(their_messages) * 0.3:
            example_msg = their_positive_msgs[0] if their_positive_msgs else "messages"
            indicators = ', '.join(set(positive_indicators_found[:5]))
            
            all_suggestions.append({
                'category': 'Positive Engagement',
                'priority': 'Info',
                'suggestion': f'Excellent! They\'re using positive language like "{indicators}" in messages like: "{example_msg}". This shows they genuinely enjoy talking to you!',
                'tip': f'Keep the positive momentum! Continue discussing topics that make them use words like "{indicators}".'
            })
        
        # 6. DYNAMIC Text style enthusiasm analysis
        enthusiasm_count = 0
        low_effort_count = 0
        their_enthusiasm_examples = []
        their_low_effort_examples = []
        
        for msg in their_messages:
            msg_lower = msg['message'].lower()
            # Check for enthusiasm
            for pattern in self.text_style_patterns['enthusiasm'].values():
                if re.search(pattern, msg_lower):
                    enthusiasm_count += 1
                    their_enthusiasm_examples.append(msg['message'][:40])
                    break
            # Check for low effort
            for pattern in self.text_style_patterns['low_effort'].values():
                if re.search(pattern, msg_lower):
                    low_effort_count += 1
                    their_low_effort_examples.append(msg['message'][:20])
                    break
        
        if low_effort_count > enthusiasm_count and low_effort_count > 2:
            examples = ', '.join(their_low_effort_examples[:3])
            all_suggestions.append({
                'category': 'Response Quality',
                'priority': 'High',
                'suggestion': f'They\'re giving {low_effort_count} low-effort responses like: "{examples}". Your conversation may not be engaging enough. Try discussing topics they\'re passionate about.',
                'tip': f'Ask about their hobbies, dreams, or recent experiences. Avoid yes/no questions!'
            })
        elif enthusiasm_count > 3:
            examples = ', '.join(their_enthusiasm_examples[:2])
            all_suggestions.append({
                'category': 'Great Connection!',
                'priority': 'Info',
                'suggestion': f'Amazing! They\'re showing {enthusiasm_count} enthusiastic responses like: "{examples}". They\'re genuinely excited to talk to you!',
                'tip': f'Keep this energy! Continue exploring topics that get these excited responses.'
            })
        
        # 7. DYNAMIC Topic analysis - what works best
        high_interest_topics = []
        for i, (your_msg, their_msg) in enumerate(pairs):
            if interest_scores[i] >= 3:  # High interest
                # Extract potential topics (nouns, longer words)
                words = [w for w in your_msg.split() if len(w) > 5 and w.isalpha()]
                if words:
                    high_interest_topics.append(words[0].lower())
        
        if high_interest_topics:
            topic_counts = Counter(high_interest_topics)
            top_topic = topic_counts.most_common(1)[0][0] if topic_counts else None
            
            if top_topic:
                all_suggestions.append({
                    'category': 'Winning Topics',
                    'priority': 'Info',
                    'suggestion': f'They respond best when you mention "{top_topic}". This topic generates high engagement!',
                    'tip': f'Explore more aspects of "{top_topic}" - ask their opinions, experiences, or preferences related to it.'
                })
        
        # 8. DYNAMIC conversation flow analysis
        if len(pairs) > 5:
            # Check if interest is declining
            first_half_interest = np.mean(interest_scores[:len(interest_scores)//2])
            second_half_interest = np.mean(interest_scores[len(interest_scores)//2:])
            
            if first_half_interest > second_half_interest + 0.5:
                all_suggestions.append({
                    'category': 'Interest Declining',
                    'priority': 'High',
                    'suggestion': f'Their interest dropped from {first_half_interest*25:.0f}% to {second_half_interest*25:.0f}% as conversation progressed. You may be losing their attention.',
                    'tip': f'Switch topics! Introduce something fresh and exciting to re-engage them.'
                })
            elif second_half_interest > first_half_interest + 0.5:
                all_suggestions.append({
                    'category': 'Building Momentum',
                    'priority': 'Info',
                    'suggestion': f'Their interest grew from {first_half_interest*25:.0f}% to {second_half_interest*25:.0f}%! The conversation is getting better!',
                    'tip': f'You\'re warming up nicely! Keep this trajectory by deepening the current topics.'
                })
        
        # 9. If still don't have enough suggestions, add smart fallbacks based on data
        if len(all_suggestions) < 2:
            # Analyze response time patterns (if timestamps available)
            avg_interest = np.mean(interest_scores)
            
            if avg_interest >= 3:
                all_suggestions.append({
                    'category': 'Strong Connection',
                    'priority': 'Info',
                    'suggestion': f'Overall interest is {avg_interest/4*100:.0f}%! You\'re doing great. They enjoy talking to you.',
                    'tip': 'Keep being authentic and curious. Build on what\'s working!'
                })
            elif avg_interest < 2:
                all_suggestions.append({
                    'category': 'Needs Improvement',
                    'priority': 'High',
                    'suggestion': f'Overall interest is {avg_interest/4*100:.0f}%. The conversation needs more energy.',
                    'tip': 'Try being more playful, ask deeper questions, or share interesting stories!'
                })
        
        # Prioritize and return top 3 suggestions
        # Sort by priority: High > Medium > Low > Info
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2, 'Info': 3}
        all_suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        # Return 2-3 most important suggestions
        return all_suggestions[:3]
    
    def _sentiment_compound(self, text: str) -> float:
        """Real-time VADER compound sentiment for a single message (-1..1)."""
        if not self.sentiment or not text:
            return 0.0
        try:
            return self.sentiment.polarity_scores(text)['compound']
        except Exception:
            return 0.0

    def _analyze_sentiment(self, their_messages: List[Dict], pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Live sentiment read of the other person's messages and their reaction
        to yours. Produces an engagement percentage and a trajectory (warming
        up / cooling off) computed straight from the language.
        """
        compounds = [self._sentiment_compound(m['message']) for m in their_messages]
        compounds = [c for c in compounds if c is not None]

        if not compounds:
            return {
                'available': VADER_AVAILABLE,
                'their_sentiment_score': 50.0,
                'positivity': 50.0,
                'negativity': 0.0,
                'trajectory': 'steady',
                'trajectory_delta': 0.0,
                'engagement_percentage': 50.0,
            }

        avg_compound = float(np.mean(compounds))
        # Map -1..1 to 0..100
        sentiment_pct = round((avg_compound + 1) / 2 * 100, 1)

        positive = sum(1 for c in compounds if c >= 0.2)
        negative = sum(1 for c in compounds if c <= -0.2)
        positivity = round(positive / len(compounds) * 100, 1)
        negativity = round(negative / len(compounds) * 100, 1)

        # Trajectory: compare first vs second half sentiment
        half = max(1, len(compounds) // 2)
        first_half = float(np.mean(compounds[:half]))
        second_half = float(np.mean(compounds[half:]))
        delta = round((second_half - first_half) * 100, 1)
        if delta > 12:
            trajectory = 'warming up'
        elif delta < -12:
            trajectory = 'cooling off'
        else:
            trajectory = 'steady'

        # Sentiment toward YOUR messages specifically (their reply to you)
        reply_compounds = [self._sentiment_compound(their) for _, their in pairs]
        reply_compounds = [c for c in reply_compounds if c is not None]
        reply_pct = round((float(np.mean(reply_compounds)) + 1) / 2 * 100, 1) if reply_compounds else sentiment_pct

        return {
            'available': VADER_AVAILABLE,
            'their_sentiment_score': sentiment_pct,
            'reply_sentiment_score': reply_pct,
            'positivity': positivity,
            'negativity': negativity,
            'trajectory': trajectory,
            'trajectory_delta': delta,
            'engagement_percentage': round((sentiment_pct * 0.6 + reply_pct * 0.4), 1),
            'interpretation': self._interpret_sentiment(sentiment_pct, positivity, trajectory),
        }

    def _interpret_sentiment(self, sentiment_pct: float, positivity: float, trajectory: str) -> str:
        if sentiment_pct >= 70:
            base = "Their language is warm and positive"
        elif sentiment_pct >= 55:
            base = "Their tone leans positive"
        elif sentiment_pct >= 45:
            base = "Their tone is fairly neutral"
        else:
            base = "Their tone reads flat or guarded"
        if trajectory == 'warming up':
            return f"{base}, and it's warming up as the chat goes on."
        if trajectory == 'cooling off':
            return f"{base}, but it's cooling off over time."
        return f"{base}."

    def format_analysis_as_text(self, analysis_result: Dict[str, Any]) -> str:
        """
        Convert analysis result JSON to beautiful human-readable text format
        """
        
        lines = []
        lines.append("=" * 80)
        lines.append("🎯 CONVERSATION ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Interest Level
        interest_pct = analysis_result.get('interest_percentage', 0)
        interpretation = analysis_result.get('interest_interpretation', 'Unknown')
        confidence = analysis_result.get('confidence_level', 0)
        
        lines.append("📊 OVERALL INTEREST LEVEL")
        lines.append("-" * 80)
        lines.append(f"   Interest Score:     {interest_pct:.1f}%")
        lines.append(f"   Interpretation:     {interpretation}")
        lines.append(f"   Confidence:         {confidence:.1f}%")
        lines.append("")
        
        # Interest breakdown with visual bar
        if interest_pct >= 80:
            bar = "█" * 40
            emoji = "🔥"
        elif interest_pct >= 60:
            bar = "█" * 30 + "▓" * 10
            emoji = "😊"
        elif interest_pct >= 40:
            bar = "█" * 20 + "▓" * 10 + "░" * 10
            emoji = "😐"
        elif interest_pct >= 20:
            bar = "█" * 10 + "▓" * 10 + "░" * 20
            emoji = "😕"
        else:
            bar = "█" * 5 + "░" * 35
            emoji = "😞"
        
        lines.append(f"   Visual:  [{bar}] {emoji}")
        lines.append("")
        
        # Percentage breakdown
        if 'percentage_breakdown' in analysis_result:
            breakdown = analysis_result['percentage_breakdown']
            lines.append("📈 DETAILED BREAKDOWN")
            lines.append("-" * 80)
            lines.append(f"   Their Engagement:       {breakdown.get('their_engagement_score', 0):.1f}%")
            lines.append(f"   Conversation Quality:   {breakdown.get('conversation_quality', 0):.1f}%")
            lines.append(f"   Compatibility Score:    {breakdown.get('compatibility_score', 0):.1f}%")
            lines.append("")
        
        # Sentiment Analysis (real-time VADER)
        if 'sentiment_analysis' in analysis_result and analysis_result['sentiment_analysis'].get('available'):
            sent = analysis_result['sentiment_analysis']
            lines.append("🧠 LIVE SENTIMENT ANALYSIS")
            lines.append("-" * 80)
            lines.append(f"   Their Sentiment:        {sent.get('their_sentiment_score', 0):.1f}%")
            lines.append(f"   Reaction To You:        {sent.get('reply_sentiment_score', 0):.1f}%")
            lines.append(f"   Positive Messages:      {sent.get('positivity', 0):.1f}%")
            lines.append(f"   Negative Messages:      {sent.get('negativity', 0):.1f}%")
            lines.append(f"   Trajectory:             {sent.get('trajectory', 'steady').title()} ({sent.get('trajectory_delta', 0):+.0f})")
            lines.append(f"   📝 {sent.get('interpretation', 'N/A')}")
            lines.append("")

        # Text Style Analysis
        if 'text_style_analysis' in analysis_result:
            text_style = analysis_result['text_style_analysis']
            lines.append("💬 TEXT STYLE ANALYSIS")
            lines.append("-" * 80)
            lines.append(f"   Enthusiasm Patterns:    {text_style.get('enthusiasm_patterns', 0)} detected")
            lines.append(f"   Enthusiasm Level:       {text_style.get('enthusiasm_percentage', 0):.1f}%")
            lines.append(f"   Low-Effort Responses:   {text_style.get('low_effort_responses', 0)} found")
            lines.append(f"   Style Score:            {text_style.get('style_score', 0):.1f}%")
            lines.append(f"   📝 {text_style.get('interpretation', 'N/A')}")
            lines.append("")
        
        # Emoji Analysis
        if 'emoji_analysis' in analysis_result:
            emoji_data = analysis_result['emoji_analysis']
            lines.append("😊 EMOJI ANALYSIS")
            lines.append("-" * 80)
            lines.append(f"   Total Emojis Used:      {emoji_data.get('total_emojis', 0)}")
            lines.append(f"   Usage Rate:             {emoji_data.get('emoji_usage_rate', 0):.1f}%")
            lines.append(f"   Positive Emojis:        {emoji_data.get('positive_emoji_percentage', 0):.1f}%")
            lines.append(f"   Emoji Diversity:        {emoji_data.get('emoji_diversity', 0):.1f}%")
            lines.append(f"   😊 {emoji_data.get('interpretation', 'N/A')}")
            lines.append("")
        
        # Engagement metrics
        if 'engagement_metrics' in analysis_result:
            metrics = analysis_result['engagement_metrics']
            lines.append("🔥 ENGAGEMENT METRICS")
            lines.append("-" * 80)
            lines.append(f"   Your Avg Message Length:    {metrics.get('your_avg_message_length', 0)} words")
            lines.append(f"   Their Avg Message Length:   {metrics.get('their_avg_message_length', 0)} words")
            lines.append(f"   Response Length Ratio:      {metrics.get('response_length_ratio', 0):.2f}x")
            lines.append(f"   Your Questions Asked:       {metrics.get('your_questions_asked', 0)}")
            lines.append(f"   Their Questions Asked:      {metrics.get('their_questions_asked', 0)}")
            lines.append(f"   Question Reciprocation:     {metrics.get('question_reciprocation_rate', 0):.2f}x")
            lines.append(f"   Your Emoji Usage:           {metrics.get('your_emoji_usage', 0)}")
            lines.append(f"   Their Emoji Usage:          {metrics.get('their_emoji_usage', 0)}")
            lines.append(f"   Engagement Balance:         {metrics.get('engagement_balance', 0):.2f}")
            lines.append("")
        
        # Improvement suggestions
        if 'improvement_suggestions' in analysis_result:
            suggestions = analysis_result['improvement_suggestions']
            lines.append("💡 PERSONALIZED SUGGESTIONS")
            lines.append("=" * 80)
            
            for i, suggestion in enumerate(suggestions, 1):
                priority = suggestion.get('priority', 'Medium')
                category = suggestion.get('category', 'General')
                
                # Priority emoji
                if priority == 'High':
                    priority_emoji = "🔴"
                elif priority == 'Medium':
                    priority_emoji = "🟡"
                else:
                    priority_emoji = "🟢"
                
                lines.append("")
                lines.append(f"{i}. {priority_emoji} {category} [{priority} Priority]")
                lines.append("-" * 80)
                lines.append(f"   {suggestion.get('suggestion', 'N/A')}")
                lines.append("")
                lines.append(f"   💎 Pro Tip: {suggestion.get('tip', 'N/A')}")
                lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("✨ END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def create_and_save_model(save_path: str = None):
    """
    Create a new conversation interest model and save it
    """
    model = ConversationInterestAnalyzer()
    
    if save_path is None:
        save_path = os.path.join(
            os.path.dirname(__file__),
            'trained',
            'conversation_interest_model.pth'
        )
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Save model
    torch.save(model.state_dict(), save_path)
    print(f"✅ Model saved to: {save_path}")
    
    return model, save_path


if __name__ == "__main__":
    # Create and save initial model
    model, path = create_and_save_model()
    print(f"🎯 Conversation Interest Model created")
    print(f"📁 Saved to: {path}")
