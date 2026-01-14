/**
 * Ukkonen's Suffix Tree Implementation
 * 
 * Features:
 * - O(n) construction using Ukkonen's algorithm
 * - Incremental string addition with unique separators
 * - JSON serialization/deserialization
 * - Fragment search
 */

class SuffixTreeNode {
  constructor(start = -1, end = null) {
    this.children = new Map();
    this.suffixLink = null;
    this.start = start;
    this.end = end; // null means "leaf" - uses global end
    this.suffixIndex = -1; // For leaf nodes: position in text where this suffix starts
  }

  getEdgeLength(globalEnd) {
    const endVal = this.end === null ? globalEnd : this.end;
    return endVal - this.start;
  }
}

class SuffixTree {
  /**
   * Create a new SuffixTree
   * @param {Object|null} serialized - Optional serialized tree data to restore from
   */
  constructor(serialized = null) {
    if (serialized) {
      this._deserialize(serialized);
    } else {
      this._initializeEmpty();
    }
  }

  /**
   * Initialize an empty tree
   * @private
   */
  _initializeEmpty() {
    this.text = '';
    this.strings = []; // Array of {text, startIndex, endIndex, id}
    this.root = new SuffixTreeNode(-1, -1);
    this.root.suffixLink = this.root;
    
    // Ukkonen's algorithm state
    this.activeNode = this.root;
    this.activeEdge = -1;
    this.activeLength = 0;
    this.remainingSuffixCount = 0;
    this.leafEnd = 0;
    
    // String separators tracking
    this.separatorPositions = new Set();
    this.nextStringId = 0;
    
    // Flag to track if tree was restored (suffix links may be incomplete)
    this._needsRebuild = false;
  }

  /**
   * Add a string to the suffix tree incrementally
   * @param {string} str - The string to add
   * @param {string|null} id - Optional identifier for this string
   * @returns {string} The ID assigned to this string
   */
  addString(str, id = null) {
    if (!str || str.length === 0) {
      throw new Error('Cannot add empty string');
    }

    // If tree was restored from serialization, we need to rebuild it
    // because suffix links are incomplete
    if (this._needsRebuild) {
      this._rebuildTreeFromStrings();
    }

    const stringId = id !== null ? id : `str_${this.nextStringId}`;
    this.nextStringId++;

    // Add separator if this isn't the first string
    if (this.text.length > 0) {
      // Use a unique separator character
      const separator = String.fromCharCode(0xE000 + this.strings.length - 1);
      this.separatorPositions.add(this.text.length);
      this.text += separator;
      this._extendTreeByChar();
    }

    const textStartIndex = this.text.length;

    // Add each character of the string
    for (const char of str) {
      this.text += char;
      this._extendTreeByChar();
    }

    // Add terminal character unique to this string
    const terminator = String.fromCharCode(0xF000 + this.strings.length);
    this.separatorPositions.add(this.text.length);
    this.text += terminator;
    this._extendTreeByChar();

    this.strings.push({
      text: str,
      startIndex: textStartIndex,
      endIndex: this.text.length - 1, // Position of terminator
      id: stringId
    });

    return stringId;
  }

  /**
   * Rebuild the tree from scratch using stored strings
   * Called when adding to a deserialized tree
   * @private
   */
  _rebuildTreeFromStrings() {
    const savedStrings = this.strings.slice();
    
    // Reset to empty state
    this.text = '';
    this.strings = [];
    this.root = new SuffixTreeNode(-1, -1);
    this.root.suffixLink = this.root;
    this.activeNode = this.root;
    this.activeEdge = -1;
    this.activeLength = 0;
    this.remainingSuffixCount = 0;
    this.leafEnd = 0;
    this.separatorPositions = new Set();
    this._needsRebuild = false;
    
    // Re-add all existing strings
    for (const strInfo of savedStrings) {
      // Use internal add logic without incrementing nextStringId again
      const stringId = strInfo.id;
      
      // Add separator if this isn't the first string
      if (this.text.length > 0) {
        const separator = String.fromCharCode(0xE000 + this.strings.length - 1);
        this.separatorPositions.add(this.text.length);
        this.text += separator;
        this._extendTreeByChar();
      }

      const textStartIndex = this.text.length;

      // Add each character of the string
      for (const char of strInfo.text) {
        this.text += char;
        this._extendTreeByChar();
      }

      // Add terminal character unique to this string
      const terminator = String.fromCharCode(0xF000 + this.strings.length);
      this.separatorPositions.add(this.text.length);
      this.text += terminator;
      this._extendTreeByChar();

      this.strings.push({
        text: strInfo.text,
        startIndex: textStartIndex,
        endIndex: this.text.length - 1,
        id: stringId
      });
    }
  }

  /**
   * Extend the suffix tree by one character (Ukkonen's algorithm)
   * @private
   */
  _extendTreeByChar() {
    const pos = this.text.length - 1;
    this.leafEnd = this.text.length;
    this.remainingSuffixCount++;
    let lastNewNode = null;

    while (this.remainingSuffixCount > 0) {
      if (this.activeLength === 0) {
        this.activeEdge = pos;
      }

      const activeEdgeChar = this.text[this.activeEdge];
      
      if (!this.activeNode.children.has(activeEdgeChar)) {
        // Rule 2: Create new leaf
        const newLeaf = new SuffixTreeNode(pos, null);
        newLeaf.suffixIndex = pos - this.remainingSuffixCount + 1;
        this.activeNode.children.set(activeEdgeChar, newLeaf);

        if (lastNewNode !== null) {
          lastNewNode.suffixLink = this.activeNode;
          lastNewNode = null;
        }
      } else {
        const next = this.activeNode.children.get(activeEdgeChar);
        const edgeLength = next.getEdgeLength(this.leafEnd);

        // Walk down if needed (skip/count trick)
        if (this.activeLength >= edgeLength) {
          this.activeEdge += edgeLength;
          this.activeLength -= edgeLength;
          this.activeNode = next;
          continue;
        }

        // Rule 3: Character already exists on edge (showstopper)
        if (this.text[next.start + this.activeLength] === this.text[pos]) {
          if (lastNewNode !== null && this.activeNode !== this.root) {
            lastNewNode.suffixLink = this.activeNode;
            lastNewNode = null;
          }
          this.activeLength++;
          break;
        }

        // Rule 2 with split: Split the edge
        const splitEnd = next.start + this.activeLength;
        const splitNode = new SuffixTreeNode(next.start, splitEnd);
        this.activeNode.children.set(activeEdgeChar, splitNode);
        
        // New leaf from split point
        const newLeaf = new SuffixTreeNode(pos, null);
        newLeaf.suffixIndex = pos - this.remainingSuffixCount + 1;
        splitNode.children.set(this.text[pos], newLeaf);
        
        // Existing node continues after split
        next.start = splitEnd;
        splitNode.children.set(this.text[splitEnd], next);

        if (lastNewNode !== null) {
          lastNewNode.suffixLink = splitNode;
        }
        lastNewNode = splitNode;
      }

      this.remainingSuffixCount--;

      if (this.activeNode === this.root && this.activeLength > 0) {
        this.activeLength--;
        this.activeEdge = pos - this.remainingSuffixCount + 1;
      } else if (this.activeNode !== this.root) {
        this.activeNode = this.activeNode.suffixLink || this.root;
      }
    }
  }

  /**
   * Search for all occurrences of a pattern
   * @param {string} pattern - The pattern to search for
   * @param {Object} options - Search options
   * @param {number} options.limit - Maximum number of results to return (default: 100)
   * @param {boolean} options.includePosition - Include position information (default: true)
   * @returns {Object} Search result with matches array and truncated flag
   *   - matches: Array of match objects
   *   - truncated: Boolean indicating if there were more matches than the limit
   *   - totalFound: Total number of matches found (before limiting)
   */
  search(pattern, options = {}) {
    const { limit = 100, includePosition = true } = options;
    
    if (!pattern || pattern.length === 0) {
      return { matches: [], truncated: false, totalFound: 0 };
    }

    // Find the node where pattern ends
    const searchResult = this._findPattern(pattern);
    if (!searchResult) {
      return { matches: [], truncated: false, totalFound: 0 };
    }

    const { node } = searchResult;

    // Collect all suffix indices from the subtree
    const suffixIndices = [];
    this._collectSuffixIndices(node, suffixIndices);

    // Build results
    const matches = [];
    const seen = new Set();

    for (const suffixStart of suffixIndices) {
      // The match occurs at suffixStart
      const matchStart = suffixStart;
      const matchEnd = matchStart + pattern.length;

      // Find which original string this belongs to
      const stringInfo = this._getStringInfo(matchStart);
      if (!stringInfo) continue;

      // Skip if match extends beyond this string or crosses a separator
      if (matchEnd > stringInfo.endIndex) continue;
      if (this._crossesSeparator(matchStart, matchEnd)) continue;

      const localStart = matchStart - stringInfo.startIndex;
      const localEnd = localStart + pattern.length;
      
      // Verify the matched text
      const matchedText = stringInfo.text.substring(localStart, localEnd);
      if (matchedText !== pattern) continue; // Safety check

      const key = `${stringInfo.id}:${localStart}`;
      if (seen.has(key)) continue;
      seen.add(key);

      const result = {
        stringId: stringInfo.id,
        match: pattern,
        matchedText: matchedText,
        context: stringInfo.text,
        localPosition: localStart
      };

      if (includePosition) {
        result.globalPosition = matchStart;
      }

      matches.push(result);
    }

    const totalFound = matches.length;
    const truncated = totalFound > limit;
    
    return {
      matches: matches.slice(0, limit),
      truncated,
      totalFound
    };
  }

  /**
   * Find a pattern in the tree, returning the node where it ends
   * @private
   */
  _findPattern(pattern) {
    let node = this.root;
    let i = 0;

    while (i < pattern.length) {
      const char = pattern[i];
      
      if (!node.children.has(char)) {
        return null; // Pattern not found
      }
      
      const child = node.children.get(char);
      const edgeStart = child.start;
      const edgeEnd = child.end === null ? this.leafEnd : child.end;
      const edgeLength = edgeEnd - edgeStart;
      
      // Compare pattern with edge label
      let j = 0;
      while (j < edgeLength && i < pattern.length) {
        if (this.text[edgeStart + j] !== pattern[i]) {
          return null; // Mismatch
        }
        j++;
        i++;
      }
      
      if (i === pattern.length) {
        // Pattern fully matched
        return { node: child, matchedInEdge: j, edgeLength };
      }
      
      // Continue to next node
      node = child;
    }

    return { node, matchedInEdge: 0, edgeLength: 0 };
  }

  /**
   * Collect all suffix indices from a subtree
   * @private
   */
  _collectSuffixIndices(node, indices) {
    if (node.suffixIndex >= 0) {
      // Leaf node
      indices.push(node.suffixIndex);
      return;
    }

    for (const child of node.children.values()) {
      this._collectSuffixIndices(child, indices);
    }
  }

  /**
   * Calculate match score based on surrounding context
   * @private
   */
  _calculateMatchScore(text, position, matchLength) {
    let score = text.length * 10;
    
    // Bonus for word boundary matches
    const beforeChar = position > 0 ? text[position - 1] : ' ';
    const afterPos = position + matchLength;
    const afterChar = afterPos < text.length ? text[afterPos] : ' ';
    
    if (/[\s\.,;:!?\-]/.test(beforeChar)) score += 100;
    if (/[\s\.,;:!?\-]/.test(afterChar)) score += 100;
    
    // Bonus for matches at start of string
    if (position === 0) score += 50;
    
    return score;
  }

  /**
   * Get string info for a position in the concatenated text
   * @private
   */
  _getStringInfo(position) {
    for (const str of this.strings) {
      if (position >= str.startIndex && position < str.endIndex) {
        return str;
      }
    }
    return null;
  }

  /**
   * Check if a range crosses a separator
   * @private
   */
  _crossesSeparator(start, end) {
    for (const sepPos of this.separatorPositions) {
      if (sepPos > start && sepPos < end) {
        return true;
      }
    }
    return false;
  }

  /**
   * Export the suffix tree to a serializable format
   * @returns {Object} Serialized tree data
   */
  export() {
    return {
      version: 1,
      text: this.text,
      strings: this.strings.map(s => ({
        text: s.text,
        startIndex: s.startIndex,
        endIndex: s.endIndex,
        id: s.id
      })),
      separatorPositions: Array.from(this.separatorPositions),
      nextStringId: this.nextStringId,
      leafEnd: this.leafEnd,
      tree: this._serializeNode(this.root)
    };
  }

  /**
   * Serialize a node and its children
   * @private
   */
  _serializeNode(node) {
    const children = {};
    for (const [char, child] of node.children) {
      children[char] = this._serializeNode(child);
    }

    return {
      start: node.start,
      end: node.end,
      suffixIndex: node.suffixIndex,
      children: children
    };
  }

  /**
   * Deserialize tree from exported data
   * @private
   */
  _deserialize(data) {
    if (data.version !== 1) {
      throw new Error(`Unsupported serialization version: ${data.version}`);
    }

    this.text = data.text;
    this.strings = data.strings;
    this.separatorPositions = new Set(data.separatorPositions);
    this.nextStringId = data.nextStringId;
    this.leafEnd = data.leafEnd;

    // Rebuild tree structure
    this.root = this._deserializeNode(data.tree);
    this.root.suffixLink = this.root;

    // Rebuild suffix links (simplified - all point to root)
    this._rebuildSuffixLinks();

    // Reset active state
    this.activeNode = this.root;
    this.activeEdge = -1;
    this.activeLength = 0;
    this.remainingSuffixCount = 0;
    
    // Mark that tree needs rebuild if new strings are added
    // (because suffix links are incomplete)
    this._needsRebuild = true;
  }

  /**
   * Deserialize a node
   * @private
   */
  _deserializeNode(data) {
    const node = new SuffixTreeNode(data.start, data.end);
    node.suffixIndex = data.suffixIndex;

    for (const [char, childData] of Object.entries(data.children)) {
      node.children.set(char, this._deserializeNode(childData));
    }

    return node;
  }

  /**
   * Rebuild suffix links after deserialization
   * @private
   */
  _rebuildSuffixLinks() {
    // Point all internal nodes to root (simplified, sufficient for search)
    const queue = [this.root];
    
    while (queue.length > 0) {
      const node = queue.shift();
      if (node !== this.root && node.suffixIndex < 0) {
        node.suffixLink = this.root;
      }
      
      for (const child of node.children.values()) {
        queue.push(child);
      }
    }
  }

  /**
   * Get statistics about the tree
   * @returns {Object} Tree statistics
   */
  getStats() {
    let nodeCount = 0;
    let leafCount = 0;
    let maxDepth = 0;

    const countNodes = (node, depth) => {
      nodeCount++;
      if (node.suffixIndex >= 0) {
        leafCount++;
        maxDepth = Math.max(maxDepth, depth);
      }
      for (const child of node.children.values()) {
        countNodes(child, depth + 1);
      }
    };

    countNodes(this.root, 0);

    return {
      totalTextLength: this.text.length,
      stringCount: this.strings.length,
      nodeCount,
      leafCount,
      maxDepth,
      strings: this.strings.map(s => ({ id: s.id, length: s.text.length }))
    };
  }

  /**
   * Check if tree contains a pattern
   * @param {string} pattern - Pattern to check
   * @returns {boolean} True if pattern exists in tree
   */
  contains(pattern) {
    return this._findPattern(pattern) !== null;
  }

  /**
   * Count occurrences of a pattern
   * @param {string} pattern - Pattern to count
   * @returns {number} Number of occurrences
   */
  count(pattern) {
    const result = this._findPattern(pattern);
    if (!result) return 0;
    
    const indices = [];
    this._collectSuffixIndices(result.node, indices);
    
    // Filter out matches that cross separators
    let count = 0;
    for (const idx of indices) {
      if (!this._crossesSeparator(idx, idx + pattern.length)) {
        count++;
      }
    }
    return count;
  }
}

// ES6 exports
export { SuffixTree, SuffixTreeNode };

// CommonJS support
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SuffixTree, SuffixTreeNode };
}

// Global for browser
if (typeof window !== 'undefined') {
  window.SuffixTree = SuffixTree;
  window.SuffixTreeNode = SuffixTreeNode;
}
