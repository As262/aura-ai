"""
Conversation Decoder Module
Supports: PDF, TXT, JSON, CSV, LOG formats
Extracts conversation data for ML analysis
"""

import json
import csv
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Try to import PyPDF2, provide fallback if not available
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2 not available. PDF support disabled. Install with: pip install PyPDF2")


class ConversationDecoder:
    """
    Multi-format conversation file decoder
    Supports: PDF, TXT, JSON, CSV, LOG
    """
    
    def __init__(self):
        self.supported_formats = ['pdf', 'txt', 'json', 'csv', 'log']
        
    def decode_file(self, file_path: str, file_format: str = None) -> Dict[str, Any]:
        """
        Decode conversation file based on format
        
        Args:
            file_path: Path to conversation file
            file_format: File format (auto-detected if None)
            
        Returns:
            Dict with 'messages' and 'metadata'
        """
        if file_format is None:
            file_format = file_path.split('.')[-1].lower()
            
        if file_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_format}")
            
        decoder_map = {
            'pdf': self.decode_pdf,
            'txt': self.decode_txt,
            'json': self.decode_json,
            'csv': self.decode_csv,
            'log': self.decode_log
        }
        
        return decoder_map[file_format](file_path)
    
    def decode_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract conversation from PDF file
        Supports WhatsApp, Instagram, Telegram export formats
        """
        if not PDF_AVAILABLE:
            raise ImportError(
                "PDF support not available. Install PyPDF2: pip install PyPDF2"
            )
        
        messages = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Parse text into messages
            messages = self._parse_text_to_messages(text)
            
            return {
                'messages': messages,
                'metadata': {
                    'source': 'pdf',
                    'total_messages': len(messages),
                    'pages': len(pdf_reader.pages)
                }
            }
        except Exception as e:
            raise Exception(f"Failed to decode PDF: {str(e)}. Ensure the PDF contains text (not images).")
    
    def decode_txt(self, file_path: str) -> Dict[str, Any]:
        """
        Extract conversation from TXT file
        Supports multiple chat export formats
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        messages = self._parse_text_to_messages(text)
        
        return {
            'messages': messages,
            'metadata': {
                'source': 'txt',
                'total_messages': len(messages)
            }
        }
    
    def decode_json(self, file_path: str) -> Dict[str, Any]:
        """
        Extract conversation from JSON file
        Expected format: [{"sender": "...", "message": "...", "timestamp": "..."}, ...]
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        messages = []
        
        # Handle different JSON structures
        if isinstance(data, list):
            for item in data:
                message = self._normalize_json_message(item)
                if message:
                    messages.append(message)
        elif isinstance(data, dict):
            # Handle nested structures
            if 'messages' in data:
                for item in data['messages']:
                    message = self._normalize_json_message(item)
                    if message:
                        messages.append(message)
            elif 'conversation' in data:
                for item in data['conversation']:
                    message = self._normalize_json_message(item)
                    if message:
                        messages.append(message)
        
        return {
            'messages': messages,
            'metadata': {
                'source': 'json',
                'total_messages': len(messages)
            }
        }
    
    def decode_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Extract conversation from CSV file
        Expected columns: timestamp, sender, message (or similar)
        """
        messages = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                message = self._normalize_csv_row(row)
                if message:
                    messages.append(message)
        
        return {
            'messages': messages,
            'metadata': {
                'source': 'csv',
                'total_messages': len(messages)
            }
        }
    
    def decode_log(self, file_path: str) -> Dict[str, Any]:
        """
        Extract conversation from LOG file
        Common in chat exports and system logs
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        messages = self._parse_text_to_messages(text)
        
        return {
            'messages': messages,
            'metadata': {
                'source': 'log',
                'total_messages': len(messages)
            }
        }
    
    def _parse_text_to_messages(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse plain text into structured messages
        Supports multiple chat formats (WhatsApp, Telegram, Instagram)
        """
        messages = []
        
        # Common patterns for chat exports
        patterns = [
            # WhatsApp: [DD/MM/YYYY, HH:MM:SS] Sender: Message
            r'\[(\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.+)',
            # WhatsApp alternative: DD/MM/YYYY, HH:MM - Sender: Message
            r'(\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2})\s+-\s+([^:]+):\s+(.+)',
            # Telegram: [HH:MM:SS] Sender: Message
            r'\[(\d{2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.+)',
            # Instagram: Sender • HH:MM Message
            r'([^\•]+)\s+•\s+(\d{2}:\d{2})\s+(.+)',
            # Generic: Sender: Message
            r'^([^:]+):\s+(.+)$'
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        timestamp, sender, message = groups
                    elif len(groups) == 2:
                        sender, message = groups
                        timestamp = None
                    else:
                        continue
                    
                    messages.append({
                        'timestamp': timestamp,
                        'sender': sender.strip(),
                        'message': message.strip()
                    })
                    matched = True
                    break
            
            # If no pattern matched, try simple sender: message format
            if not matched and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    messages.append({
                        'timestamp': None,
                        'sender': parts[0].strip(),
                        'message': parts[1].strip()
                    })
        
        return messages
    
    def _normalize_json_message(self, item: Dict) -> Dict[str, Any]:
        """Normalize JSON message to standard format"""
        # Try different possible key names
        sender_keys = ['sender', 'from', 'user', 'name', 'author']
        message_keys = ['message', 'text', 'content', 'body']
        timestamp_keys = ['timestamp', 'time', 'date', 'created_at']
        
        sender = None
        message = None
        timestamp = None
        
        for key in sender_keys:
            if key in item:
                sender = item[key]
                break
        
        for key in message_keys:
            if key in item:
                message = item[key]
                break
        
        for key in timestamp_keys:
            if key in item:
                timestamp = item[key]
                break
        
        if sender and message:
            return {
                'timestamp': timestamp,
                'sender': str(sender),
                'message': str(message)
            }
        
        return None
    
    def _normalize_csv_row(self, row: Dict) -> Dict[str, Any]:
        """Normalize CSV row to standard format"""
        # Try different column name variations
        sender_keys = ['sender', 'from', 'user', 'name', 'author']
        message_keys = ['message', 'text', 'content', 'body']
        timestamp_keys = ['timestamp', 'time', 'date', 'created_at']
        
        # Case-insensitive search
        row_lower = {k.lower(): v for k, v in row.items()}
        
        sender = None
        message = None
        timestamp = None
        
        for key in sender_keys:
            if key in row_lower:
                sender = row_lower[key]
                break
        
        for key in message_keys:
            if key in row_lower:
                message = row_lower[key]
                break
        
        for key in timestamp_keys:
            if key in row_lower:
                timestamp = row_lower[key]
                break
        
        if sender and message:
            return {
                'timestamp': timestamp,
                'sender': sender,
                'message': message
            }
        
        return None
    
    def extract_conversation_pairs(self, messages: List[Dict]) -> List[Tuple[str, str]]:
        """
        Extract conversation pairs (you -> other) for interest analysis
        
        Returns:
            List of (your_message, their_response) tuples
        """
        if not messages or len(messages) < 2:
            return []
        
        # Identify the two main participants
        senders = {}
        for msg in messages:
            sender = msg['sender']
            senders[sender] = senders.get(sender, 0) + 1
        
        # Get top 2 senders
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if len(top_senders) < 2:
            return []
        
        user1, user2 = top_senders[0][0], top_senders[1][0]
        
        # Extract pairs
        pairs = []
        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]
            
            # User1 -> User2 or User2 -> User1
            if (current['sender'] == user1 and next_msg['sender'] == user2) or \
               (current['sender'] == user2 and next_msg['sender'] == user1):
                pairs.append((
                    current['message'],
                    next_msg['message']
                ))
        
        return pairs


# Utility function for backward compatibility
def decode_conversation_file(file_path: str, file_format: str = None) -> Dict[str, Any]:
    """
    Decode conversation file - convenience function
    """
    decoder = ConversationDecoder()
    return decoder.decode_file(file_path, file_format)
