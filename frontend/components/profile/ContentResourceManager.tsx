// ---
// File Path: frontend/components/profile/ContentResourceManager.tsx
// ---

'use client';

import { useState, useEffect, FC } from 'react';
import { Plus, Trash2, Edit3, Save, XCircle, ExternalLink, BookOpen, Video, FileText, Sparkles } from 'lucide-react';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

export interface ContentResource {
  id: string;
  title: string;
  url: string;
  description?: string;
  categories: string[];
  content_type: 'article' | 'video' | 'document';
  status: 'active' | 'inactive' | 'archived';
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface ContentResourceCreate {
  title: string;
  url: string;
  description?: string;
  categories: string[];
  content_type: 'article' | 'video' | 'document';
}

interface ContentResourceManagerProps {
  api: any; // API client from context
}

export const ContentResourceManager: FC<ContentResourceManagerProps> = ({ api }) => {
  const [resources, setResources] = useState<ContentResource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });
  
  // Form state for adding/editing
  const [formData, setFormData] = useState<ContentResourceCreate>({
    title: '',
    url: '',
    description: '',
    categories: [],
    content_type: 'article'
  });
  
  const [newCategory, setNewCategory] = useState('');

  // Add window size tracking for confetti
  useEffect(() => {
    const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Load resources on component mount
  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get('/api/content-resources/');
      setResources(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load content resources');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddResource = async () => {
    if (!formData.title.trim() || !formData.url.trim()) {
      setError('Title and URL are required');
      return;
    }

    try {
      const newResource = await api.post('/api/content-resources/', formData);
      setResources(prev => [newResource, ...prev]);
      setIsAdding(false);
      setFormData({
        title: '',
        url: '',
        description: '',
        categories: [],
        content_type: 'article'
      });
      setError(null);
      
      // Show confetti for successful resource addition
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 7000);
    } catch (err: any) {
      setError(err.message || 'Failed to add resource');
    }
  };

  const handleUpdateResource = async (id: string) => {
    try {
      const updatedResource = await api.put(`/api/content-resources/${id}`, formData);
      setResources(prev => prev.map(r => r.id === id ? updatedResource : r));
      setEditingId(null);
      setFormData({
        title: '',
        url: '',
        description: '',
        categories: [],
        content_type: 'article'
      });
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update resource');
    }
  };

  const handleDeleteResource = async (id: string) => {
    try {
      await api.del(`/api/content-resources/${id}`);
      setResources(prev => prev.filter(r => r.id !== id));
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete resource');
    }
  };

  const startEditing = (resource: ContentResource) => {
    setEditingId(resource.id);
    setFormData({
      title: resource.title,
      url: resource.url,
      description: resource.description || '',
      categories: resource.categories,
      content_type: resource.content_type
    });
  };

  const cancelEditing = () => {
    setEditingId(null);
    setIsAdding(false);
    setFormData({
      title: '',
      url: '',
      description: '',
      categories: [],
      content_type: 'article'
    });
    setError(null);
  };

  const addCategory = () => {
    if (newCategory.trim() && !formData.categories.includes(newCategory.trim())) {
      setFormData(prev => ({
        ...prev,
        categories: [...prev.categories, newCategory.trim().toLowerCase()]
      }));
      setNewCategory('');
    }
  };

  const removeCategory = (category: string) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.filter(c => c !== category)
    }));
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video size={16} />;
      case 'document': return <FileText size={16} />;
      default: return <BookOpen size={16} />;
    }
  };

  const getContentTypeColor = (type: string) => {
    switch (type) {
      case 'video': return 'text-purple-400';
      case 'document': return 'text-orange-400';
      default: return 'text-blue-400';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Content Resources</h3>
        </div>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mx-auto"></div>
          <p className="text-gray-400 mt-2">Loading resources...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Confetti for successful content resource addition */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={600}
          tweenDuration={7000}
          colors={[
            ACTIVE_THEME.primary.from,
            ACTIVE_THEME.primary.to,
            ACTIVE_THEME.accent,
            ACTIVE_THEME.action,
            '#ffffff'
          ]}
        />
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            Content Resources
          </h3>
          <button
            onClick={() => setIsAdding(true)}
            className="px-3 py-1.5 text-sm font-semibold bg-white/10 rounded-lg hover:bg-white/20 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Resource
          </button>
        </div>
        
        <p className="text-sm text-gray-400">
          Add helpful content that your AI can share with clients based on their interests and needs.
        </p>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-white font-medium">
                {editingId ? 'Edit Resource' : 'Add New Resource'}
              </h4>
              <button
                onClick={cancelEditing}
                className="text-gray-400 hover:text-white"
              >
                <XCircle size={20} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                  placeholder="Enter resource title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">URL *</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                  placeholder="https://example.com/resource"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 resize-none"
                placeholder="Brief description of the resource"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Content Type</label>
                <select
                  value={formData.content_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, content_type: e.target.value as any }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                >
                  <option value="article">Article</option>
                  <option value="video">Video</option>
                  <option value="document">Document</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Categories</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCategory()}
                    className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                    placeholder="Add category"
                  />
                  <button
                    onClick={addCategory}
                    className="px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg text-sm"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Categories Display */}
            {formData.categories.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Current Categories</label>
                <div className="flex flex-wrap gap-2">
                  {formData.categories.map((category) => (
                    <span
                      key={category}
                      className="flex items-center gap-1 bg-teal-600/20 text-teal-300 px-2 py-1 rounded-md text-sm"
                    >
                      {category}
                      <button
                        onClick={() => removeCategory(category)}
                        className="text-teal-400 hover:text-teal-200"
                      >
                        <XCircle size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <button
                onClick={cancelEditing}
                className="px-4 py-2 text-gray-300 hover:text-white border border-gray-600 rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => editingId ? handleUpdateResource(editingId) : handleAddResource()}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-medium"
              >
                {editingId ? <><Save size={16} className="inline mr-1" /> Update</> : <><Plus size={16} className="inline mr-1" /> Add Resource</>}
              </button>
            </div>
          </div>
        )}

        {/* Resources List */}
        <div className="space-y-3">
          {resources.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No content resources yet</p>
              <p className="text-sm">Add your first resource to start sharing helpful content with clients</p>
            </div>
          ) : (
            resources.map((resource) => (
              <div
                key={resource.id}
                className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`${getContentTypeColor(resource.content_type)}`}>
                        {getContentTypeIcon(resource.content_type)}
                      </span>
                      <h4 className="font-medium text-white">{resource.title}</h4>
                      <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
                        {resource.content_type}
                      </span>
                    </div>
                    
                    {resource.description && (
                      <p className="text-gray-300 text-sm mb-2">{resource.description}</p>
                    )}
                    
                    <div className="flex items-center gap-2 mb-3">
                      <a
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal-400 hover:text-teal-300 text-sm flex items-center gap-1"
                      >
                        <ExternalLink size={14} />
                        View Resource
                      </a>
                      <span className="text-gray-500 text-sm">•</span>
                      <span className="text-gray-400 text-sm">
                        Used {resource.usage_count} time{resource.usage_count !== 1 ? 's' : ''}
                      </span>
                    </div>

                    {resource.categories.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {resource.categories.map((category) => (
                          <span
                            key={category}
                            className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs"
                          >
                            {category}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => startEditing(resource)}
                      className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded"
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      onClick={() => handleDeleteResource(resource.id)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}; 