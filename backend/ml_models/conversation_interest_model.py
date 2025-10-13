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


class ConversationInterestAnalyzer(nn.Module):
    """
    Neural network for analyzing conversation interest and engagement
    Features: response time, message length, emoji usage, question patterns
    """
    
    def __init__(self, input_size=50, hidden_size=128, output_size=5):
        super(ConversationInterestAnalyzer, self).__init__()
        
        # Network architecture
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.bn2 = nn.BatchNorm1d(hidden_size // 2)
        self.dropout2 = nn.Dropout(0.2)
        
        self.fc3 = nn.Linear(hidden_size // 2, output_size)
        
        # Interest level categories
        self.interest_categories = [
            "Very Low",
            "Low", 
            "Moderate",
            "High",
            "Very High"
        ]
        
    def forward(self, x):
        """Forward pass through the network"""
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        x = self.fc3(x)
        return x


class ConversationAnalysisService:
    """
    Service for comprehensive conversation analysis
    """
    
    def __init__(self, model_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ConversationInterestAnalyzer().to(self.device)
        
        if model_path and os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
        
        # Engagement indicators
        self.positive_indicators = [
            'haha', 'lol', 'lmao', '😂', '😊', '❤️', '🥰', '😍', '!', 
            'really', 'wow', 'amazing', 'awesome', 'cool', 'nice', 'great'
        ]
        
        self.negative_indicators = [
            'ok', 'k', 'hmm', 'idk', 'whatever', 'sure', 'fine', 'maybe'
        ]
        
        self.question_patterns = [
            r'\?$',  # Ends with ?
            r'^(what|when|where|why|how|who|which)',  # Question words
            r'^(do|does|did|can|could|would|should|will)',  # Auxiliary verbs
        ]
    
    def extract_features(self, your_message: str, their_response: str) -> np.ndarray:
        """
        Extract features from message pair for ML analysis
        
        Returns 50-dimensional feature vector
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
        
        # Ensure we have exactly 50 features
        while len(features) < 50:
            features.append(0.0)
        
        return np.array(features[:50], dtype=np.float32)
    
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
        
        # Calculate overall statistics
        avg_interest = np.mean(interest_scores)
        interest_distribution = Counter(interest_scores)
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(pairs, interest_scores, your_messages, their_messages)
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(
            your_messages, their_messages, pairs
        )
        
        return {
            'overall_interest_level': self.model.interest_categories[int(round(avg_interest))],
            'average_interest_score': round(avg_interest, 2),
            'interest_percentage': round((avg_interest / 4) * 100, 2),  # 0-4 scale to 0-100
            'interest_distribution': {
                self.model.interest_categories[i]: interest_distribution.get(i, 0)
                for i in range(5)
            },
            'total_messages': len(messages),
            'your_messages': len(your_messages),
            'their_messages': len(their_messages),
            'conversation_pairs_analyzed': len(pairs),
            'engagement_metrics': engagement_metrics,
            'detailed_pair_analysis': detailed_pairs[:10],  # First 10 pairs
            'improvement_suggestions': suggestions,
            'participants': {
                'you': user,
                'other_person': other
            }
        }
    
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
                            their_messages: List[Dict]) -> List[Dict[str, str]]:
        """Generate personalized improvement suggestions - always returns 2-3 tips"""
        
        all_suggestions = []
        
        # Analyze low interest pairs
        low_interest_pairs = [pairs[i] for i, score in enumerate(interest_scores) if score <= 1]
        
        if len(low_interest_pairs) > len(pairs) * 0.4:
            all_suggestions.append({
                'category': 'Overall Engagement',
                'priority': 'High',
                'suggestion': f'Over 40% of your messages received low-interest responses. Try asking more open-ended questions and showing genuine curiosity about their interests.',
                'tip': 'Instead of "Did you like it?", try "What did you think about it? I\'d love to hear your perspective!"'
            })
        
        # Message length analysis
        your_avg = np.mean([len(msg['message'].split()) for msg in your_messages])
        their_avg = np.mean([len(msg['message'].split()) for msg in their_messages])
        
        if your_avg > their_avg * 2:
            all_suggestions.append({
                'category': 'Message Length',
                'priority': 'Medium',
                'suggestion': 'Your messages are significantly longer than theirs. Try being more concise and giving them more space to contribute.',
                'tip': 'Break long messages into smaller parts and ask questions to keep the conversation flowing.'
            })
        elif your_avg < their_avg * 0.5:
            all_suggestions.append({
                'category': 'Message Length',
                'priority': 'Medium',
                'suggestion': 'Your messages are quite short. Try elaborating more to show you\'re invested in the conversation.',
                'tip': 'Add your thoughts, feelings, or follow-up questions to make your responses more engaging.'
            })
        
        # Question analysis
        your_questions = sum(1 for msg in your_messages if '?' in msg['message'])
        their_questions = sum(1 for msg in their_messages if '?' in msg['message'])
        
        if your_questions < len(your_messages) * 0.2:
            all_suggestions.append({
                'category': 'Curiosity & Questions',
                'priority': 'High',
                'suggestion': 'You\'re not asking many questions. Show more interest by asking about their day, opinions, and experiences.',
                'tip': 'Use the 5 W\'s: Who, What, When, Where, Why (and How!) to keep conversations dynamic.'
            })
        
        if their_questions < len(their_messages) * 0.15:
            all_suggestions.append({
                'category': 'Engagement',
                'priority': 'Medium',
                'suggestion': 'They\'re not asking many questions back. Try sharing interesting stories or experiences that naturally invite questions.',
                'tip': 'Leave conversational "hooks" - mention something intriguing without full details to spark curiosity.'
            })
        
        # Emoji usage
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        your_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in your_messages)
        their_emojis = sum(len(emoji_pattern.findall(msg['message'])) for msg in their_messages)
        
        if your_emojis < len(your_messages) * 0.3 and their_emojis > len(their_messages) * 0.5:
            all_suggestions.append({
                'category': 'Expressiveness',
                'priority': 'Low',
                'suggestion': 'They use emojis frequently, but you don\'t. Match their communication style by adding more emojis to show emotion.',
                'tip': 'Use emojis to convey tone - 😊 for friendly, 😂 for funny, ❤️ for appreciation.'
            })
        
        # Positive indicators
        their_positive = sum(
            sum(1 for indicator in self.positive_indicators 
                if indicator in msg['message'].lower())
            for msg in their_messages
        )
        
        if their_positive > len(their_messages) * 0.3:
            all_suggestions.append({
                'category': 'Positive Signs',
                'priority': 'Info',
                'suggestion': 'Great news! They\'re using lots of positive language (lol, haha, etc.), which shows they enjoy talking to you.',
                'tip': 'Keep doing what you\'re doing, but continue to evolve the conversation topics to maintain interest.'
            })
        
        # Always add these general tips to ensure we have at least 2-3 suggestions
        general_suggestions = [
            {
                'category': 'Overall',
                'priority': 'Info',
                'suggestion': 'Your conversation shows good engagement! Keep being yourself and showing genuine interest.',
                'tip': 'Continue building on shared interests and asking thoughtful questions.'
            },
            {
                'category': 'Growth',
                'priority': 'Low',
                'suggestion': 'Try introducing new topics occasionally to keep conversations fresh and exciting.',
                'tip': 'Share interesting things you learned, funny stories, or ask for their opinion on current events.'
            },
            {
                'category': 'Timing',
                'priority': 'Low',
                'suggestion': 'Pay attention to response times and conversation flow to keep momentum going.',
                'tip': 'Match their energy level and response pace for better conversation rhythm.'
            }
        ]
        
        # Add general suggestions if we don't have enough specific ones
        for suggestion in general_suggestions:
            if len(all_suggestions) >= 3:
                break
            if suggestion not in all_suggestions:
                all_suggestions.append(suggestion)
        
        # Prioritize and return top 2-3 suggestions
        # Sort by priority: High > Medium > Low > Info
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2, 'Info': 3}
        all_suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        # Return 2-3 most important suggestions
        return all_suggestions[:3]


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
