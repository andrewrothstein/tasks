#!/bin/bash

echo "Let's automate setting up your React project for the AI Agent Prompt Library!"

#read -p "Enter your desired project name (e.g., my-ai-library): " PROJECT_NAME
PROJECT_NAME="ai-agent-prompt-library"
echo "Using default project name: $PROJECT_NAME"
# Check if Node.js and npm are installed

if [ -z "$PROJECT_NAME" ]; then
  echo "Project name cannot be empty. Exiting."
  exit 1
fi

echo "Creating a new React project with Create React App..."
npx create-react-app "$PROJECT_NAME" || { echo "Failed to create React app. Do you have Node.js and npm/npx installed?"; exit 1; }

cd "$PROJECT_NAME" || { echo "Failed to navigate into $PROJECT_NAME. Exiting."; exit 1; }

echo "Installing Firebase..."
npm install firebase || { echo "Failed to install Firebase. Exiting."; exit 1; }

echo "Replacing src/App.js with the provided AI Agent Prompt Library code..."

# The content of src/App.js is embedded here.
# NOTE: You MUST manually insert your Gemini API Key and Firebase Config
# after the script finishes, as these cannot be automated by this script.
cat << 'EOF' > src/App.js
import React, { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, collection, addDoc, query, orderBy, onSnapshot, serverTimestamp, getDocs } from 'firebase/firestore';

// Main App component for the AI Agent Prompt Library
function App() {
  // State variables for managing application data and UI
  const [prompt, setPrompt] = useState(''); // Current prompt input by the user
  const [response, setResponse] = useState('Your AI agent is ready. Ask me anything!'); // AI's current response
  const [loading, setLoading] = useState(false); // Loading indicator for AI generation
  const [searchQuery, setSearchQuery] = useState(''); // Search query for the prompt library
  const [searchResults, setSearchResults] = useState([]); // Results from searching the prompt library
  const [message, setMessage] = useState(''); // General messages to the user (e.g., errors, success)
  const [userId, setUserId] = useState(null); // Current authenticated user ID
  const [allPrompts, setAllPrompts] = useState([]); // All prompts and responses stored in Firestore
  const [db, setDb] = useState(null); // Firestore database instance
  const [auth, setAuth] = useState(null); // Firebase Auth instance
  const [isAuthReady, setIsAuthReady] = useState(false); // Flag to indicate if Firebase Auth is ready

  // Ref for the message box to control its visibility
  const messageBoxRef = useRef(null);

  // Constants for Firebase configuration and API key
  // These variables (appId, firebaseConfig) are normally provided by the Canvas environment.
  // For your local setup, you need to replace them with your actual Firebase project configuration.
  const appId = "YOUR_FIREBASE_APP_ID"; // e.g., "your-project-id" from Firebase console -> Project settings
  const firebaseConfig = { // e.g., from Firebase console -> Project settings -> Your apps -> Firebase SDK snippet
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "YOUR_FIREBASE_AUTH_DOMAIN",
    projectId: "YOUR_FIREBASE_PROJECT_ID",
    storageBucket: "YOUR_FIREBASE_STORAGE_BUCKET",
    messagingSenderId: "YOUR_FIREBASE_MESSAGING_SENDER_ID",
    appId: "YOUR_FIREBASE_APP_ID",
    measurementId: "YOUR_FIREBASE_MEASUREMENT_ID"
  };

  // IMPORTANT: For 'embedding-001' model, you need to provide your own Gemini API key here.
  // Obtain this from Google AI Studio or Google Cloud Console.
  const apiKey = ""; // <--- INSERT YOUR GEMINI API KEY HERE FOR EMBEDDING-001

  // Configuration object for "magic numbers"
  const config = {
    chunkSize: 500, // Size of text chunks for embedding
    contextLimit: 3, // Number of relevant past interactions to use as context for new prompts
  };

  // Helper function to display messages to the user in a custom message box
  const showMessage = (msg, type = 'info') => {
    setMessage(msg);
    if (messageBoxRef.current) {
      messageBoxRef.current.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'}`;
      messageBoxRef.current.style.display = 'block';
      // Automatically hide the message after 3 seconds
      setTimeout(() => {
        if (messageBoxRef.current) {
          messageBoxRef.current.style.display = 'none';
        }
      }, 3000);
    }
  };

  // Helper function to generate embeddings using the Gemini API
  const generateEmbedding = async (text) => {
    if (!text || text.trim() === '') {
      console.warn("Attempted to generate embedding for empty or null text.");
      return null; // Return null for empty text to avoid API call
    }

    // Check if API key is provided for embedding model
    if (!apiKey) {
      showMessage('API Key is missing for embedding-001 model. Please insert your API key in src/App.js.', 'error');
      console.error('API Key is missing for embedding-001 model.');
      return null;
    }

    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=${apiKey}`;
    const payload = {
      model: "models/embedding-001",
      content: { parts: [{ text: text }] }
    };

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      // Check if the HTTP response itself was successful
      if (!response.ok) {
        const errorBody = await response.text(); // Get raw response body for more info
        throw new Error(`HTTP error! Status: ${response.status}, Message: ${response.statusText}. Body: ${errorBody}`);
      }

      const result = await response.json();
      console.log("Embedding API raw result:", result); // Log the full result for debugging

      if (result.embedding && result.embedding.values) {
        return result.embedding.values;
      } else if (result.error) {
        // If API returns a structured error object, extract its message
        const errorMessage = result.error.message || JSON.stringify(result.error);
        throw new Error(`Embedding API error: ${errorMessage}`);
      } else {
        throw new Error("Embedding API response missing embedding values or error object.");
      }
    } catch (error) {
      console.error("Error generating embedding:", error);
      // Ensure error message is always a string
      const errorMessage = error.message || JSON.stringify(error) || 'Unknown error during embedding generation.';
      showMessage(`Error generating embedding: ${errorMessage}`, 'error');
      return null;
    }
  };

  // Helper function to chunk text
  const chunkText = (text) => {
    const chunks = [];
    for (let i = 0; i < text.length; i += config.chunkSize) {
      chunks.push(text.substring(i, i + config.chunkSize));
    }
    return chunks;
  };

  // Helper function to calculate cosine similarity between two vectors
  const cosineSimilarity = (vecA, vecB) => {
    if (!vecA || !vecB || vecA.length !== vecB.length) {
      return 0;
    }
    let dotProduct = 0;
    let magnitudeA = 0;
    let magnitudeB = 0;
    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
      magnitudeA += vecA[i] * vecA[i];
      magnitudeB += vecB[i] * vecB[i];
    }
    magnitudeA = Math.sqrt(magnitudeA);
    magnitudeB = Math.sqrt(magnitudeB);
    if (magnitudeA === 0 || magnitudeB === 0) {
      return 0;
    }
    return dotProduct / (magnitudeA * magnitudeB);
  };

  // useEffect hook for Firebase initialization and authentication
  useEffect(() => {
    try {
      // Initialize Firebase app
      const app = initializeApp(firebaseConfig);
      const firestoreDb = getFirestore(app);
      const firebaseAuth = getAuth(app);

      setDb(firestoreDb);
      setAuth(firebaseAuth);

      // Listen for authentication state changes
      const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
        if (user) {
          // User is signed in, set userId
          setUserId(user.uid);
        } else {
          // No user is signed in, sign in anonymously if no initial token
          // In a standalone app, you would typically use other auth methods (e.g., signInWithEmailAndPassword, signInWithPopup)
          // For anonymous use, signInAnonymously is fine.
          signInAnonymously(firebaseAuth)
            .then(() => {
              setUserId(firebaseAuth.currentUser?.uid);
            })
            .catch((error) => {
              console.error("Error signing in anonymously:", error);
              showMessage(`Authentication error: ${error.message}`, 'error');
            });
        }
        setIsAuthReady(true); // Set auth ready flag
      });

      // Cleanup function for auth listener
      return () => unsubscribe();
    } catch (error) {
      console.error("Error initializing Firebase:", error);
      showMessage(`Error initializing Firebase: ${error.message}`);
    }
  }, [JSON.stringify(firebaseConfig)]); // Depend on firebaseConfig to re-run if it changes (though usually static)

  // useEffect hook for fetching all prompts from Firestore in real-time
  useEffect(() => {
    if (!db || !userId || !isAuthReady) return; // Only run if db, userId, and auth are ready

    try {
      // Define the collection path for private user data
      const userPromptsCollectionRef = collection(db, `artifacts/${appId}/users/${userId}/prompt_library`);
      // Create a query to order by timestamp (most recent first)
      const q = query(userPromptsCollectionRef, orderBy('timestamp', 'desc'));

      // Set up a real-time listener for the prompt library
      const unsubscribe = onSnapshot(q, (snapshot) => {
        const promptsData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setAllPrompts(promptsData); // Update state with all prompts
      }, (error) => {
        console.error("Error fetching prompts:", error);
        showMessage(`Error fetching past prompts: ${error.message}`);
      });

      // Cleanup function for the snapshot listener
      return () => unsubscribe();
    } catch (error) {
      console.error("Error setting up Firestore listener:", error);
      showMessage(`Error setting up prompt listener: ${error.message}`);
    }
  }, [db, userId, isAuthReady, appId]); // Dependencies: db, userId, isAuthReady, appId

  // Function to handle prompt submission
  const handlePromptSubmit = async () => {
    if (!prompt.trim()) {
      showMessage('Please enter a prompt.', 'error');
      return;
    }
    if (!db || !userId) {
      showMessage('Firebase not initialized or user not authenticated. Please wait.', 'error');
      return;
    }

    setLoading(true); // Show loading indicator
    setResponse('Thinking...'); // Clear previous response and show thinking message

    let chatHistory = [];
    let contextPrompts = [];

    // Generate embedding for the current prompt to find relevant past interactions
    const currentPromptEmbedding = await generateEmbedding(prompt);

    if (currentPromptEmbedding) {
      // Perform vector search to find semantically similar past prompts
      const relevantChunks = [];
      allPrompts.forEach(item => {
        item.chunks?.forEach(chunk => {
          if (chunk.embedding) {
            const similarity = cosineSimilarity(currentPromptEmbedding, chunk.embedding);
            relevantChunks.push({
              similarity,
              promptId: item.id,
              promptText: item.prompt,
              responseText: item.response,
              chunkText: chunk.text
            });
          }
        });
      });

      // Sort by similarity and get top `config.contextLimit` unique prompt-response pairs for context
      relevantChunks.sort((a, b) => b.similarity - a.similarity);
      const uniqueContexts = new Map(); // Use Map to maintain order and uniqueness
      for (const chunk of relevantChunks) {
        if (!uniqueContexts.has(chunk.promptId)) {
          uniqueContexts.set(chunk.promptId, `Past Prompt: ${chunk.promptText}\nPast Response: ${chunk.responseText}`);
          if (uniqueContexts.size >= config.contextLimit) break; // Limit to top relevant contexts
        }
      }
      contextPrompts = Array.from(uniqueContexts.values());
    }

    // Add past context to the chat history
    if (contextPrompts.length > 0) {
      chatHistory.push({ role: "system", parts: [{ text: "Here are some of our past interactions for context:\n" + contextPrompts.join('\n\n') }] });
    }

    // Add the current user prompt
    chatHistory.push({ role: "user", parts: [{ text: prompt }] });

    const payload = { contents: chatHistory };
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

    try {
      // Make the API call to Gemini
      const apiResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await apiResponse.json();

      // Process the Gemini response
      if (result.candidates && result.candidates.length > 0 &&
          result.candidates[0].content && result.candidates[0].content.parts &&
          result.candidates[0].content.parts.length > 0) {
        const aiResponseText = result.candidates[0].content.parts[0].text;
        setResponse(aiResponseText); // Update AI response in UI

        // Prepare data for Firestore, including chunks and embeddings
        const combinedText = `${prompt}\n${aiResponseText}`;
        const textChunks = chunkText(combinedText);
        const embeddedChunks = [];

        // Generate embeddings for each chunk
        for (const chunk of textChunks) {
          const embedding = await generateEmbedding(chunk);
          if (embedding) {
            embeddedChunks.push({ text: chunk, embedding: embedding });
          }
        }

        // Store the prompt, response, and embedded chunks in Firestore
        await addDoc(collection(db, `artifacts/${appId}/users/${userId}/prompt_library`), {
          prompt: prompt,
          response: aiResponseText,
          timestamp: serverTimestamp(), // Use server timestamp for consistent ordering
          chunks: embeddedChunks // Store chunks with their embeddings
        });
        setPrompt(''); // Clear the prompt input
        showMessage('Prompt and response saved!', 'info');
      } else {
        const errorMessage = result.error?.message || 'Unexpected API response structure.';
        setResponse(`Error: ${errorMessage}`);
        showMessage(`AI response error: ${errorMessage}`, 'error');
        console.error("Unexpected API response:", result);
      }
    } catch (error) {
      console.error("Error calling Gemini API:", error);
      setResponse(`Error: ${error.message}`);
      showMessage(`Failed to get AI response: ${error.message}`, 'error');
    } finally {
      setLoading(false); // Hide loading indicator
    }
  };

  // Function to handle searching the prompt library using vector search
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]); // Clear search results if query is empty
      return;
    }

    setLoading(true); // Show loading indicator for search
    setSearchResults([]); // Clear previous search results

    const queryEmbedding = await generateEmbedding(searchQuery);

    if (!queryEmbedding) {
      setLoading(false);
      return;
    }

    const scoredResults = [];
    allPrompts.forEach(item => {
      let maxSimilarity = 0;
      item.chunks?.forEach(chunk => {
        if (chunk.embedding) {
          const similarity = cosineSimilarity(queryEmbedding, chunk.embedding);
          if (similarity > maxSimilarity) {
            maxSimilarity = similarity;
          }
        }
      });
      if (maxSimilarity > 0) { // Only include if there's some similarity
        scoredResults.push({ ...item, score: maxSimilarity });
      }
    });

    // Sort results by similarity score (descending)
    scoredResults.sort((a, b) => b.score - a.score);

    // Filter for a reasonable similarity threshold if desired, or just show top N
    // For now, let's just show all relevant results sorted.
    setSearchResults(scoredResults);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4 font-sans text-gray-800">
      {/* Tailwind CSS configuration for Inter font */}
      <style>
        {`
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
          body {
            font-family: 'Inter', sans-serif;
          }
        `}
      </style>

      {/* Main container for the AI Agent */}
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-4xl mb-8">
        <h1 className="text-4xl font-bold text-center text-blue-700 mb-6">AI Agent Prompt Library</h1>

        {/* User ID Display */}
        {userId && (
          <p className="text-sm text-gray-500 text-center mb-4">
            Logged in as: <span className="font-semibold text-blue-600 break-all">{userId}</span>
          </p>
        )}

        {/* Prompt Input Section */}
        <div className="mb-6">
          <label htmlFor="prompt-input" className="block text-lg font-medium text-gray-700 mb-2">
            Enter your prompt:
          </label>
          <textarea
            id="prompt-input"
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out resize-y min-h-[100px]"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Explain quantum computing in simple terms."
            rows="4"
          ></textarea>
          <button
            onClick={handlePromptSubmit}
            className="mt-4 w-full bg-blue-600 text-white py-3 px-6 rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out font-semibold text-lg"
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Ask AI Agent'}
          </button>
        </div>

        {/* AI Response Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-700 mb-3">AI Response:</h2>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 shadow-inner">
            <p className="text-gray-800 whitespace-pre-wrap">{response}</p>
          </div>
        </div>

        {/* Search Prompt Library Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-700 mb-3">Search Prompt Library:</h2>
          <div className="flex space-x-3">
            <input
              type="text"
              className="flex-grow p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
              placeholder="Search past prompts and responses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => { if (e.key === 'Enter') handleSearch(); }}
            />
            <button
              onClick={handleSearch}
              className="bg-green-600 text-white py-3 px-6 rounded-lg shadow-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition duration-200 ease-in-out font-semibold"
              disabled={loading}
            >
              Search
            </button>
          </div>

          {/* Search Results Display */}
          {searchResults.length > 0 && (
            <div className="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-200 shadow-inner max-h-96 overflow-y-auto">
              <h3 className="text-xl font-medium text-gray-700 mb-3">Search Results ({searchResults.length}):</h3>
              {searchResults.map((item) => (
                <div key={item.id} className="mb-4 p-3 border border-gray-200 rounded-lg bg-white shadow-sm">
                  <p className="font-semibold text-blue-600 mb-1">Prompt:</p>
                  <p className="text-gray-800 mb-2 whitespace-pre-wrap">{item.prompt}</p>
                  <p className="font-semibold text-green-600 mb-1">Response:</p>
                  <p className="text-gray-800 whitespace-pre-wrap">{item.response}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {item.timestamp ? new Date(item.timestamp.toDate()).toLocaleString() : 'Loading date...'}
                  </p>
                  {item.score && <p className="text-xs text-gray-400">Similarity Score: {item.score.toFixed(4)}</p>}
                </div>
              ))}
            </div>
          )}
          {searchQuery.trim() && searchResults.length === 0 && !loading && (
            <p className="mt-4 text-gray-600 text-center">No results found for "{searchQuery}".</p>
          )}
        </div>

        {/* All Prompts Library Display */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-700 mb-3">Your Full Prompt Library:</h2>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 shadow-inner max-h-96 overflow-y-auto">
            {allPrompts.length === 0 && !loading ? (
              <p className="text-gray-600 text-center">Your prompt library is empty. Start by asking the AI agent a question!</p>
            ) : (
              allPrompts.map((item) => (
                <div key={item.id} className="mb-4 p-3 border border-gray-200 rounded-lg bg-white shadow-sm">
                  <p className="font-semibold text-blue-600 mb-1">Prompt:</p>
                  <p className="text-gray-800 mb-2 whitespace-pre-wrap">{item.prompt}</p>
                  <p className="font-semibold text-green-600 mb-1">Response:</p>
                  <p className="text-gray-800 whitespace-pre-wrap">{item.response}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {item.timestamp ? new Date(item.timestamp.toDate()).toLocaleString() : 'Loading date...'}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Custom Message Box */}
      <div
        ref={messageBoxRef}
        className="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 hidden"
        style={{ display: 'none' }}
      >
        {message}
      </div>
    </div>
  );
}

export default App;
EOF

echo "Modifying public/index.html to include Tailwind CSS and Inter font..."
# Replace the default index.html with one that includes Tailwind CDN and Inter font.
# This assumes the default structure from create-react-app.
sed -i.bak '/<div id="root">/,/<\/body>/s|<div id="root">.*<\/div>|<div id="root"></div>\
          <script>\
            tailwind.config = {\
              theme: {\
                extend: {\
                  fontFamily: {\
                    sans: [\
                      '\''Inter'\'',\
                      '\''sans-serif'\''\
                    ]\
                  }\
                }\
              }\
            }\
          </script>|' public/index.html
sed -i.bak 's|<title>.*</title>|<title>AI Agent Prompt Library</title>\
    <script src="https://cdn.tailwindcss.com"></script>\
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">|' public/index.html

echo "Project setup complete! Now you need to:"
echo "1. Navigate into your project directory: cd $PROJECT_NAME"
echo "2. Open src/App.js and replace 'YOUR_FIREBASE_APP_ID' and 'YOUR_FIREBASE_API_KEY' with your actual Firebase project configuration."
echo "3. Insert your Gemini API Key for the embedding-001 model in the 'apiKey' constant in src/App.js."
echo "4. Run your app: npm start"
echo ""
echo "Remember to visit Google AI Studio or Google Cloud Console to get your Gemini API Key and Firebase project configuration."
echo "For Firebase, also enable Firestore and Anonymous Authentication."