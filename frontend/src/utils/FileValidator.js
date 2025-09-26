// File validation and security utilities
class FileValidator {
  // Maximum file sizes by type (in bytes)
  static MAX_SIZES = {
    image: 10 * 1024 * 1024, // 10MB
    video: 100 * 1024 * 1024, // 100MB
    text: 1 * 1024 * 1024, // 1MB
    default: 5 * 1024 * 1024 // 5MB
  };

  // Allowed MIME types by category
  static ALLOWED_TYPES = {
    image: [
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/svg+xml'
    ],
    video: [
      'video/mp4',
      'video/mpeg',
      'video/quicktime',
      'video/x-msvideo',
      'video/webm',
      'video/3gpp'
    ],
    text: [
      'text/plain',
      'text/csv',
      'application/json',
      'text/log'
    ]
  };

  // Dangerous file extensions to block
  static BLOCKED_EXTENSIONS = [
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js',
    'jar', 'zip', 'rar', '7z', 'tar', 'gz', 'dmg', 'iso',
    'php', 'asp', 'aspx', 'jsp', 'py', 'rb', 'pl', 'sh'
  ];

  /**
   * Validates file based on security criteria
   * @param {File} file - File object to validate
   * @param {Object} options - Validation options
   * @returns {Object} - Validation result
   */
  static validateFile(file, options = {}) {
    const result = {
      isValid: true,
      errors: [],
      warnings: []
    };

    try {
      // Basic file existence check
      if (!file) {
        result.isValid = false;
        result.errors.push('No file provided');
        return result;
      }

      // File size validation
      const sizeValidation = this.validateFileSize(file, options);
      if (!sizeValidation.isValid) {
        result.isValid = false;
        result.errors.push(...sizeValidation.errors);
      }

      // File type validation
      const typeValidation = this.validateFileType(file, options);
      if (!typeValidation.isValid) {
        result.isValid = false;
        result.errors.push(...typeValidation.errors);
      }

      // File name validation
      const nameValidation = this.validateFileName(file);
      if (!nameValidation.isValid) {
        result.isValid = false;
        result.errors.push(...nameValidation.errors);
      }
      if (nameValidation.warnings.length > 0) {
        result.warnings.push(...nameValidation.warnings);
      }

      // Content validation (basic)
      const contentValidation = this.validateFileContent(file);
      if (!contentValidation.isValid) {
        result.isValid = false;
        result.errors.push(...contentValidation.errors);
      }

    } catch (error) {
      result.isValid = false;
      result.errors.push(`Validation error: ${error.message}`);
    }

    return result;
  }

  /**
   * Validates file size
   */
  static validateFileSize(file, options) {
    const result = { isValid: true, errors: [] };
    
    const fileType = this.getFileCategory(file.type);
    const maxSize = options.maxSize || this.MAX_SIZES[fileType] || this.MAX_SIZES.default;

    if (file.size > maxSize) {
      result.isValid = false;
      result.errors.push(
        `File size (${this.formatFileSize(file.size)}) exceeds maximum allowed size (${this.formatFileSize(maxSize)})`
      );
    }

    if (file.size === 0) {
      result.isValid = false;
      result.errors.push('File appears to be empty');
    }

    return result;
  }

  /**
   * Validates file type and MIME type
   */
  static validateFileType(file, options) {
    const result = { isValid: true, errors: [] };
    
    // Check if file type is allowed
    const allowedTypes = options.allowedTypes || this.getAllowedTypes(options.category);
    
    if (allowedTypes && allowedTypes.length > 0) {
      const isAllowed = allowedTypes.some(allowedType => {
        // Handle wildcard types like "image/*"
        if (allowedType.endsWith('/*')) {
          const baseType = allowedType.slice(0, -2);
          return file.type.startsWith(baseType + '/');
        }
        // Handle exact matches
        return file.type === allowedType;
      });
      
      if (!isAllowed) {
        result.isValid = false;
        result.errors.push(`File type "${file.type}" is not allowed`);
      }
    }

    // Check MIME type vs file extension consistency
    const extension = this.getFileExtension(file.name);
    const expectedMimeTypes = this.getMimeTypesForExtension(extension);
    
    if (expectedMimeTypes.length > 0 && !expectedMimeTypes.includes(file.type)) {
      result.isValid = false;
      result.errors.push(`File extension "${extension}" doesn't match MIME type "${file.type}"`);
    }

    return result;
  }

  /**
   * Validates file name for security issues
   */
  static validateFileName(file) {
    const result = { isValid: true, errors: [], warnings: [] };
    
    const fileName = file.name;
    const extension = this.getFileExtension(fileName);

    // Check for blocked extensions
    if (this.BLOCKED_EXTENSIONS.includes(extension.toLowerCase())) {
      result.isValid = false;
      result.errors.push(`File extension "${extension}" is not allowed for security reasons`);
    }

    // Check for suspicious file names
    const suspiciousPatterns = [
      /\.(exe|bat|cmd|scr|vbs|js)$/i,
      /\.\w+\.\w+$/, // Double extensions
      /[<>:"|?*]/,   // Invalid characters
      /^\./,         // Hidden files
      /\s{2,}/       // Multiple spaces
    ];

    suspiciousPatterns.forEach(pattern => {
      if (pattern.test(fileName)) {
        result.warnings.push('File name contains potentially suspicious patterns');
      }
    });

    // Check file name length
    if (fileName.length > 255) {
      result.isValid = false;
      result.errors.push('File name is too long (maximum 255 characters)');
    }

    if (fileName.length === 0) {
      result.isValid = false;
      result.errors.push('File name is empty');
    }

    return result;
  }

  /**
   * Basic content validation
   */
  static validateFileContent(file) {
    const result = { isValid: true, errors: [] };
    
    // Check for null bytes (potential malware indicator)
    if (file.name.includes('\0')) {
      result.isValid = false;
      result.errors.push('File contains null bytes');
    }

    return result;
  }

  /**
   * Sanitizes file name for safe storage
   */
  static sanitizeFileName(fileName) {
    return fileName
      .replace(/[^a-zA-Z0-9.-]/g, '_') // Replace unsafe characters
      .replace(/_{2,}/g, '_')          // Replace multiple underscores
      .replace(/^_|_$/g, '')           // Remove leading/trailing underscores
      .substring(0, 100);              // Limit length
  }

  /**
   * Helper methods
   */
  static getFileCategory(mimeType) {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('text/') || mimeType.includes('json')) return 'text';
    return 'default';
  }

  static getFileExtension(fileName) {
    return fileName.split('.').pop() || '';
  }

  static getAllowedTypes(category) {
    if (!category) return null;
    return this.ALLOWED_TYPES[category] || null;
  }

  static getMimeTypesForExtension(extension) {
    const mimeMap = {
      'jpg': ['image/jpeg'],
      'jpeg': ['image/jpeg'],
      'png': ['image/png'],
      'gif': ['image/gif'],
      'webp': ['image/webp'],
      'svg': ['image/svg+xml'],
      'mp4': ['video/mp4'],
      'mov': ['video/quicktime'],
      'avi': ['video/x-msvideo'],
      'webm': ['video/webm'],
      'txt': ['text/plain'],
      'csv': ['text/csv'],
      'json': ['application/json'],
      'log': ['text/log']
    };

    return mimeMap[extension.toLowerCase()] || [];
  }

  static formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Advanced validation using FileReader (async)
   */
  static async validateFileContentAdvanced(file) {
    return new Promise((resolve) => {
      const result = { isValid: true, errors: [], warnings: [] };
      
      // Skip validation for large files to avoid memory issues
      if (file.size > 50 * 1024 * 1024) { // 50MB
        result.warnings.push('Skipping content validation for large file');
        resolve(result);
        return;
      }

      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const arrayBuffer = e.target.result;
          const bytes = new Uint8Array(arrayBuffer, 0, Math.min(arrayBuffer.byteLength, 512));
          
          // For images, verify they start with proper headers
          if (file.type.startsWith('image/')) {
            const isValidImage = this.validateImageHeader(bytes, file.type);
            if (!isValidImage) {
              result.isValid = false;
              result.errors.push('Invalid image file header');
            }
          }
          
          resolve(result);
        } catch (error) {
          result.warnings.push(`Content validation error: ${error.message}`);
          resolve(result);
        }
      };

      reader.onerror = () => {
        result.warnings.push('Could not read file for content validation');
        resolve(result);
      };

      reader.readAsArrayBuffer(file.slice(0, 512)); // Read first 512 bytes
    });
  }

  static validateImageHeader(bytes, mimeType) {
    const signatures = {
      'image/jpeg': [0xFF, 0xD8, 0xFF],
      'image/png': [0x89, 0x50, 0x4E, 0x47],
      'image/gif': [0x47, 0x49, 0x46, 0x38],
      'image/webp': [0x52, 0x49, 0x46, 0x46]
    };

    const signature = signatures[mimeType];
    if (!signature) return true; // Unknown type, skip validation

    for (let i = 0; i < signature.length; i++) {
      if (bytes[i] !== signature[i]) {
        return false;
      }
    }
    return true;
  }
}

export default FileValidator;