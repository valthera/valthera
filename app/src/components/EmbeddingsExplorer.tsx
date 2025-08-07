import React from 'react';

const EmbeddingsExplorer: React.FC = () => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Embeddings Explorer</h1>
        <p className="text-gray-600 mt-2">
          Explore and visualize embeddings from your video data
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-12">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Embeddings Explorer Coming Soon
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            This feature will allow you to explore and visualize embeddings from your video data, 
            helping you understand the relationships between different video segments.
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmbeddingsExplorer; 