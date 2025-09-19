// frontend/components/profile/WelcomePackManager.tsx
'use client';

import { useState, useEffect, FC } from 'react';
import {
  Loader2,
  Save,
  AlertTriangle,
  CheckCircle,
  Package,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Plus,
  Trash2
} from 'lucide-react';
import { ContentResource } from './ContentResourceManager';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';

interface WelcomePackManagerProps {
  api: any;
  allResources: ContentResource[];
  userRoles: string[];
}

type PackConfig = {
  [key: string]: string[]; // Store only resource IDs
};

const ResourceItem: FC<{
  resource: ContentResource;
  isSelected: boolean;
  onClick: () => void;
  isDisabled?: boolean;
}> = ({ resource, isSelected, onClick, isDisabled = false }) => {
  return (
    <div
      onClick={onClick}
      className={`
        p-3 mb-2 border rounded-lg cursor-pointer transition-all duration-200
        ${isSelected 
          ? 'bg-teal-500/20 border-teal-500 shadow-md' 
          : 'bg-slate-800/60 border-slate-700/70 hover:border-slate-600 hover:bg-slate-800'
        }
        ${isDisabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}
      `}
    >
      <h4 className={`text-sm font-medium truncate ${isSelected ? 'text-white' : 'text-slate-200'}`}>{resource.title}</h4>
      <p className={`text-xs truncate ${isSelected ? 'text-teal-200' : 'text-slate-400'}`}>{resource.description || 'No description'}</p>
    </div>
  );
};

const ResourceList: FC<{
  title: string;
  resources: ContentResource[];
  selected: string[];
  onSelect: (id: string) => void;
  disabledIds?: Set<string>;
}> = ({ title, resources, selected, onSelect, disabledIds = new Set() }) => {
  return (
    <div className="flex-1 flex flex-col bg-slate-900/50 border border-slate-700/50 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="text-base font-semibold text-white">{title}</h3>
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        {resources.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Package size={32} className="mb-2" />
            <p className="text-sm">No resources</p>
          </div>
        )}
        {resources.map((res) => (
          <ResourceItem
            key={res.id}
            resource={res}
            isSelected={selected.includes(res.id)}
            onClick={() => onSelect(res.id)}
            isDisabled={disabledIds.has(res.id)}
          />
        ))}
      </div>
    </div>
  );
};

export const WelcomePackManager: FC<WelcomePackManagerProps> = ({ api, allResources, userRoles }) => {
  const [packConfig, setPackConfig] = useState<PackConfig>({});
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  
  const [activeRole, setActiveRole] = useState<string | null>(userRoles[0] || null);
  const [selectedAvailable, setSelectedAvailable] = useState<string[]>([]);
  const [selectedPack, setSelectedPack] = useState<string[]>([]);
  const resourceMap = new Map(allResources.map(res => [res.id, res]));

  useEffect(() => {
    const loadConfig = async () => {
      setIsLoading(true);
      try {
        const response = await api.get('/api/content-resources/welcome-packs-config');
        const { config, message } = response;
        setPackConfig(config || {});
        setWelcomeMessage(message || '');
      } catch (error) {
        console.error('Error loading welcome pack config:', error);
        setStatus('error');
      } finally {
        setIsLoading(false);
      }
    };
    loadConfig();
  }, [api]);

  const handleSave = async () => {
    setIsSaving(true);
    setStatus('idle');
    try {
      const payload = { config: packConfig, message: welcomeMessage };
      await api.put('/api/content-resources/welcome-packs-config', payload);
      
      setStatus('success');
      setTimeout(() => setStatus('idle'), 3000);
    } catch (err: any) {
      console.error('Error saving welcome pack config:', err);
      setStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRoleChange = (role: string) => {
    setActiveRole(role);
    setSelectedAvailable([]);
    setSelectedPack([]);
  }

  const handleSelection = (listType: 'available' | 'pack', id: string) => {
    const isSelected = (listType === 'available' ? selectedAvailable : selectedPack).includes(id);
    const setter = listType === 'available' ? setSelectedAvailable : setSelectedPack;
    
    setter(prev => isSelected ? prev.filter(selId => selId !== id) : [...prev, id]);
  };

  const handleAdd = () => {
    if (!activeRole || selectedAvailable.length === 0) return;
    const currentPack = packConfig[activeRole] || [];
    const newPack = [...currentPack];
    selectedAvailable.forEach(id => {
      if (!newPack.includes(id)) {
        newPack.push(id);
      }
    });
    setPackConfig(prev => ({ ...prev, [activeRole]: newPack }));
    setSelectedAvailable([]);
  };

  const handleRemove = () => {
    if (!activeRole || selectedPack.length === 0) return;
    const currentPack = packConfig[activeRole] || [];
    const newPack = currentPack.filter(id => !selectedPack.includes(id));
    setPackConfig(prev => ({ ...prev, [activeRole]: newPack }));
    setSelectedPack([]);
  };

  const handleMove = (direction: 'up' | 'down') => {
    if (!activeRole || selectedPack.length !== 1) return;
    const selectedId = selectedPack[0];
    const currentPack = [...(packConfig[activeRole] || [])];
    const index = currentPack.indexOf(selectedId);

    if (direction === 'up' && index > 0) {
      [currentPack[index], currentPack[index - 1]] = [currentPack[index - 1], currentPack[index]];
    } else if (direction === 'down' && index < currentPack.length - 1) {
      [currentPack[index], currentPack[index + 1]] = [currentPack[index + 1], currentPack[index]];
    }
    setPackConfig(prev => ({ ...prev, [activeRole]: currentPack }));
  };

  const getDerivedLists = () => {
    if (!activeRole) {
      return { available: allResources, pack: [], packIds: new Set<string>() };
    }
    const packIds = new Set(packConfig[activeRole] || []);
    const pack = (packConfig[activeRole] || []).map(id => resourceMap.get(id)).filter(Boolean) as ContentResource[];
    // The available list now shows ALL resources, the filtering is handled by disabling items.
    return { available: allResources, pack, packIds };
  };

  const { available: availableList, pack: packList, packIds: currentPackIds } = getDerivedLists();
  
  const ActionButton: FC<{
    onClick: () => void;
    disabled?: boolean;
    children: React.ReactNode;
    ariaLabel: string;
  }> = ({ onClick, disabled = false, children, ariaLabel }) => (
    <Button
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className="bg-slate-700/50 hover:bg-slate-700 disabled:opacity-40 disabled:bg-slate-800 p-2"
    >
      {children}
    </Button>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="ml-3">Loading Welcome Pack Configuration...</span>
      </div>
    );
  }

  return (
    <div className="p-6">
        <div className="space-y-1 mb-6">
            <h3 className="text-lg font-semibold text-white">Welcome Message</h3>
            <p className="text-sm text-slate-400">
                This message will be sent along with the welcome pack resources to new clients.
            </p>
        </div>
        <Textarea
            value={welcomeMessage}
            onChange={(e) => setWelcomeMessage(e.target.value)}
            placeholder="e.g., Welcome! Here are a few resources to help you get started..."
            rows={3}
            className="bg-slate-800 border-slate-600 focus:border-teal-500 focus:ring-teal-500"
        />

      <div className="mt-8 pt-8 border-t border-slate-700/50">
        <div className="flex items-center justify-between mb-6">
            <div className="space-y-1">
                <h3 className="text-lg font-semibold text-white">Resource Configuration</h3>
                <p className="text-sm text-slate-400">
                    Select a role, then build its Welcome Pack.
                </p>
            </div>
            {userRoles.length > 0 && (
              <select 
                value={activeRole || ''} 
                onChange={(e) => handleRoleChange(e.target.value)}
                className="w-[220px] bg-slate-800 border border-slate-600 text-white rounded-lg px-3 py-2 focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
              >
                <option value="">Select a role to edit...</option>
                {userRoles.map(role => (
                  <option key={role} value={role} className="capitalize">{role}</option>
                ))}
              </select>
            )}
        </div>

        {activeRole ? (
          <div className="flex gap-4 h-[450px]">
            <ResourceList title="Available Resources" resources={availableList} selected={selectedAvailable} onSelect={(id) => handleSelection('available', id)} disabledIds={currentPackIds} />
            
            <div className="flex flex-col justify-center items-center gap-3">
              <ActionButton onClick={handleAdd} disabled={selectedAvailable.length === 0} ariaLabel="Add selected to pack"><ChevronRight size={20} /></ActionButton>
              <ActionButton onClick={handleRemove} disabled={selectedPack.length === 0} ariaLabel="Remove selected from pack"><ChevronLeft size={20} /></ActionButton>
            </div>

            <ResourceList title={`Welcome Pack for "${activeRole}"`} resources={packList} selected={selectedPack} onSelect={(id) => handleSelection('pack', id)} />

            <div className="flex flex-col justify-center items-center gap-3">
              <ActionButton onClick={() => handleMove('up')} disabled={selectedPack.length !== 1} ariaLabel="Move selected up"><ChevronUp size={20} /></ActionButton>
              <ActionButton onClick={() => handleMove('down')} disabled={selectedPack.length !== 1} ariaLabel="Move selected down"><ChevronDown size={20} /></ActionButton>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <p>Please create a client role in the "Client Organization" section to begin.</p>
          </div>
        )}
      </div>
      
      <div className="mt-8 pt-6 border-t border-slate-700/50">
        <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Click save to apply your changes to the Welcome Pack.</p>
            <div className="flex items-center space-x-4">
              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2"
              >
                {isSaving ? (<><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>) : (<><Save className="w-4 h-4" /> Save Configuration</>)}
              </Button>
              {status === 'success' && (<div className="flex items-center text-emerald-400"><CheckCircle className="w-4 h-4 mr-2" />Saved!</div>)}
              {status === 'error' && (<div className="flex items-center text-red-400"><AlertTriangle className="w-4 h-4 mr-2" />Error saving.</div>)}
            </div>
        </div>
      </div>
    </div>
  );
};