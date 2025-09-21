// ---
// File Path: frontend/components/profile/ContentResourceManager.tsx
// ---

'use client';

import { useState, useEffect, FC } from 'react';
import { Plus, Trash2, Edit3, Save, XCircle, ExternalLink, BookOpen, Video, FileText, Sparkles, Library } from 'lucide-react';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { WelcomePackManager } from './WelcomePackManager';

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
  userRoles: string[];
  allResources: ContentResource[]; // Accept the full list of resources
  onResourcesUpdate: () => void; // Callback to refresh resources
}

export const ContentResourceManager: FC<ContentResourceManagerProps> = ({ api, userRoles, allResources, onResourcesUpdate }) => {
  const [resources, setResources] = useState<ContentResource[]>(allResources);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });
  const [activeTab, setActiveTab] = useState('content');
  
  // Form state for adding/editing
  const [formData, setFormData] = useState<ContentResourceCreate>({
    title: '',
    url: '',
    description: '',
    categories: [],
    content_type: 'article'
  });
  
  const [newCategory, setNewCategory] = useState('');

  const tabOptions: TabOption[] = [
    { id: 'content', label: 'Content Library' },
    { id: 'welcomePacks', label: 'Welcome Packs' },
  ];

  // Sync state if the parent prop changes
  useEffect(() => {
    setResources(allResources);
  }, [allResources]);


  // Add window size tracking for confetti
  useEffect(() => {
    const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleAddResource = async () => {
    if (!formData.title.trim() || !formData.url.trim()) {
      setError('Title and URL are required');
      return;
    }
    setIsLoading(true);

    try {
      await api.post('/api/content-resources/', formData);
      onResourcesUpdate(); // Trigger refresh from parent
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
    } finally {
        setIsLoading(false);
    }
  };

  const handleUpdateResource = async (id: string) => {
    setIsLoading(true);
    try {
      await api.put(`/api/content-resources/${id}`, formData);
      onResourcesUpdate(); // Trigger refresh from parent
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
    } finally {
        setIsLoading(false);
    }
  };

  const handleDeleteResource = async (id: string) => {
    setIsLoading(true);
    try {
      await api.del(`/api/content-resources/${id}`);
      onResourcesUpdate(); // Trigger refresh from parent
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete resource');
    } finally {
        setIsLoading(false);
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

      <div className="bg-slate-800/40 border border-slate-600/20 rounded-2xl shadow-md w-full">
        <div className="p-6 border-b border-slate-600/20">
            <h2 className="text-xl font-bold text-white">Content & Resources</h2>
            <p className="text-sm text-slate-300 mt-1">Manage documents, links, and Welcome Packs for new clients.</p>
            <div className="mt-6">
              <Tabs options={tabOptions} activeTab={activeTab} setActiveTab={setActiveTab} />
            </div>
        </div>

        {activeTab === 'content' && (
          <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <h3 className="text-lg font-semibold text-white">
                    Content Library
                    </h3>
                    <p className="text-sm text-slate-400">
                        Add helpful content that your AI can share with clients based on their interests and needs.
                    </p>
                </div>
                <button
                  onClick={() => setIsAdding(true)}
                  className="px-4 py-2 text-sm font-medium flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg transition-colors"
                >
                  <Plus size={16} /> Add Resource
                </button>
              </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-white font-semibold text-lg">
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
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500" 
                  placeholder="e.g., Welcome Video"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">URL *</label>
                <input 
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500" 
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
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 resize-none" 
                placeholder="A brief summary of what this resource is about..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Content Type</label>
                <select 
                  value={formData.content_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, content_type: e.target.value as any }))}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                >
                  <option value="article">Article</option>
                  <option value="video">Video</option>
                  <option value="document">Document</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Categories (Tags)</label>
                <div className="flex gap-2">
                  <input 
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCategory()}
                    className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500" 
                    placeholder="Type a tag and press Enter"
                  />
                  <button 
                    onClick={addCategory}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Categories Display */}
            {formData.categories.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2">
                  {formData.categories.map((category) => (
                    <span 
                      key={category}
                      className="flex items-center gap-1.5 bg-slate-700 text-slate-200 px-2.5 py-1 rounded-full text-sm"
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
            )}

            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={cancelEditing}
                className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700/50 hover:bg-slate-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => editingId ? handleUpdateResource(editingId) : handleAddResource()}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium bg-teal-500 hover:bg-teal-600 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : (editingId ? 'Save Changes' : 'Add Resource')}
              </button>
            </div>
          </div>
        )}

              {/* Resources List */}
              <div className="space-y-3">
                {resources.length === 0 && !isAdding && !editingId ? (
                  <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
                    <Library size={40} className="mx-auto mb-4" />
                    <h4 className="text-lg font-semibold text-slate-300">Your Content Library is Empty</h4>
                    <p className="text-sm">Add your first resource to get started.</p>
                  </div>
                ) : (
                  resources.map((resource) => (
                    <div
                      key={resource.id}
                      className="bg-slate-800/60 border border-slate-700/70 rounded-lg p-4 hover:border-slate-600 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className={`p-1.5 rounded ${getContentTypeColor(resource.content_type)} bg-slate-700/50`}>
                              {getContentTypeIcon(resource.content_type)}
                            </span>
                            <h4 className="font-medium text-white">{resource.title}</h4>
                          </div>
                          
                          {resource.description && (
                            <p className="text-slate-400 text-sm mb-3 pl-10">{resource.description}</p>
                          )}
                          
                          <div className="flex items-center gap-4 pl-10">
                            <a
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-teal-400 hover:text-teal-300 text-sm flex items-center gap-1.5 transition-colors"
                            >
                              <ExternalLink size={14} />
                              View Resource
                            </a>
                            <span className="text-slate-500 text-sm">•</span>
                            <span className="text-slate-400 text-sm">
                              Used {resource.usage_count} time{resource.usage_count !== 1 ? 's' : ''}
                            </span>
                          </div>

                          {resource.categories.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-3 pl-10">
                              {resource.categories.map((category) => (
                                <span
                                  key={category}
                                  className="bg-slate-700 text-slate-300 px-2 py-1 rounded-full text-xs font-medium"
                                >
                                  {category}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex gap-1">
                          <button onClick={() => startEditing(resource)} className="p-2 text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors">
                            <Edit3 size={16} />
                          </button>
                          <button onClick={() => handleDeleteResource(resource.id)} className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
          </div>
        )}
        
        {activeTab === 'welcomePacks' && (
            <WelcomePackManager api={api} allResources={allResources} userRoles={userRoles} />
        )}
      </div>
    </>
  );
}; 