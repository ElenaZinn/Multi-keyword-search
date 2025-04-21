// Web Worker for handling search operations
self.onmessage = function(e) {
    const { text, keywords, chunkSize = 1024 * 1024 } = e.data; // 1MB chunks by default
    
    // Create regex pattern from keywords
    const pattern = keywords
        .map(keyword => `(${escapeRegExp(keyword)})`)
        .join('|');
    const regex = new RegExp(pattern, 'gi');
    
    // Process text in chunks
    const chunks = [];
    const totalChunks = Math.ceil(text.length / chunkSize);
    let processedChunks = 0;
    
    for (let i = 0; i < text.length; i += chunkSize) {
        const chunk = text.slice(i, i + chunkSize);
        const matches = [];
        let match;
        
        // Find all matches in this chunk
        while ((match = regex.exec(chunk)) !== null) {
            matches.push({
                index: i + match.index,
                text: match[0],
                length: match[0].length
            });
        }
        
        processedChunks++;
        
        // Report progress
        self.postMessage({
            type: 'progress',
            progress: (processedChunks / totalChunks) * 100,
            matches
        });
        
        chunks.push(matches);
    }
    
    // Combine all matches
    const allMatches = [].concat(...chunks);
    
    // Send final results
    self.postMessage({
        type: 'complete',
        matches: allMatches
    });
};

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
} 