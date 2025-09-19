// frontend/components/profile/WelcomePackManager.tsx
// purpose: manage the welcome pack configuration
'use client';

import { useState, useEffect, FC } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  useDroppable,
  DragStartEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Loader2, Save, AlertTriangle, CheckCircle, Package } from 'lucide-react';

import { ContentResource } from './ContentResourceManager';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';

interface WelcomePackManagerProps {
  api: any;
  allResources: ContentResource[];
  userRoles: string[];
}

type PackConfig = {
  [key: string]: ContentResource[];
};

// Draggable item component
const DraggableResourceItem: FC<{ resource: ContentResource; isOverlay?: boolean }> = ({ resource, isOverlay = false }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: resource.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging && !isOverlay ? 0.5 : 1,
    boxShadow: isOverlay ? '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)' : 'none',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center p-3 mb-2 bg-slate-700/50 border border-slate-600/50 rounded-lg transition-shadow duration-200 ${isOverlay ? 'shadow-2xl' : 'hover:bg-slate-700'}`}
      {...attributes}
    >
      <div
        className="flex items-center justify-center w-8 h-8 mr-3 text-slate-400 cursor-grab hover:text-white"
        {...listeners}
      >
        <GripVertical size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-white truncate">{resource.title}</h4>
        <p className="text-xs text-slate-400 truncate">{resource.description || "No description"}</p>
      </div>
    </div>
  );
};

// Droppable column component
const DroppableColumn: FC<{
  id: string;
  title: string;
  resources: ContentResource[];
  isLibrary?: boolean;
}> = ({ id, title, resources, isLibrary = false }) => {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <div className="flex-shrink-0 w-72 mr-6 last:mr-0">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white capitalize">{title}</h3>
        <p className="text-sm text-slate-400">
          {isLibrary ? 'Available resources' : `For ${title} clients`}
        </p>
      </div>
      <div
        ref={setNodeRef}
        className={`min-h-[400px] p-4 border-2 border-dashed rounded-xl transition-colors duration-300 ${isOver ? 'border-teal-500 bg-teal-500/10' : 'border-slate-700 bg-slate-900/50'}`}
      >
        <SortableContext items={resources.map(r => r.id)} strategy={verticalListSortingStrategy}>
          {resources.map((resource) => (
            <DraggableResourceItem key={resource.id} resource={resource} />
          ))}
        </SortableContext>
        {resources.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Package size={32} className="mb-2" />
            <p className="text-sm text-center">
              {isLibrary ? 'No available resources' : `Drop resources here for\n${title} clients`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export const WelcomePackManager: FC<WelcomePackManagerProps> = ({
  api,
  allResources,
  userRoles,
}) => {
  const [packConfig, setPackConfig] = useState<PackConfig>({});
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Initialize configuration
  useEffect(() => {
    const loadConfig = async () => {
      setIsLoading(true);
      try {
        const response = await api.get('/api/content-resources/welcome-packs-config');
        const { config, message } = response;
        
        const initialConfig: PackConfig = { library: [...allResources] };
        const assignedResourceIds = new Set<string>();

        userRoles.forEach((role) => {
          const resourceIdsForRole = config?.[role] || [];
          const resourcesForRole = resourceIdsForRole
            .map((id: string) => allResources.find(r => r.id === id))
            .filter(Boolean) as ContentResource[];
          
          initialConfig[role] = resourcesForRole;
          resourcesForRole.forEach(r => assignedResourceIds.add(r.id));
        });

        initialConfig.library = allResources.filter(r => !assignedResourceIds.has(r.id));

        setPackConfig(initialConfig);
        setWelcomeMessage(message || '');
      } catch (error) {
        console.error('Error loading welcome pack config:', error);
        setStatus('error');
      } finally {
        setIsLoading(false);
      }
    };

    if (allResources && userRoles) {
      loadConfig();
    }
  }, [api, allResources, userRoles]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;
    
    const activeId = active.id as string;
    const overId = over.id as string;

    const activeContainer = active.data.current?.sortable.containerId;
    const overContainer = over.data.current?.sortable.containerId || over.id;

    if (!activeContainer || !overContainer) return;
    
    setPackConfig((prev) => {
      const newConfig = { ...prev };
      
      if (activeContainer === overContainer) {
        // Reordering within the same column
        const activeItems = newConfig[activeContainer];
        const oldIndex = activeItems.findIndex(item => item.id === activeId);
        const newIndex = activeItems.findIndex(item => item.id === overId);

        if (oldIndex !== -1 && newIndex !== -1) {
            newConfig[activeContainer] = arrayMove(activeItems, oldIndex, newIndex);
        }
      } else {
        // Moving between columns
        const sourceItems = [...newConfig[activeContainer]];
        const destItems = [...newConfig[overContainer]];
        
        const activeIndex = sourceItems.findIndex(item => item.id === activeId);
        if (activeIndex === -1) return prev;
        
        const [movedItem] = sourceItems.splice(activeIndex, 1);
        
        const overIndex = destItems.findIndex(item => item.id === overId);
        
        if (overIndex !== -1) {
            destItems.splice(overIndex, 0, movedItem);
        } else {
            destItems.push(movedItem);
        }
        
        newConfig[activeContainer] = sourceItems;
        newConfig[overContainer] = destItems;
      }
      return newConfig;
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    setStatus('idle');

    try {
      // Transform packConfig to send only resource IDs as strings
      const configToSend: { [key: string]: string[] } = {};
      Object.entries(packConfig).forEach(([role, resources]) => {
        // Skip the library column when sending config
        if (role !== 'library') {
          // Ensure we're sending only string IDs, not the full resource objects
          configToSend[role] = resources.map(resource => resource.id);
        }
      });

      const payload = { config: configToSend, message: welcomeMessage };
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="ml-3">Loading Welcome Pack Configuration...</span>
      </div>
    );
  }

  const activeResource = activeId ? Object.values(packConfig).flat().find(r => r.id === activeId) : null;

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

      <div className="mt-8">
        <div className="space-y-1 mb-6">
            <h3 className="text-lg font-semibold text-white">Resource Configuration</h3>
            <p className="text-sm text-slate-400">
                Drag resources from the Library to the appropriate client role columns. The order you set here will be the order your client sees them.
            </p>
        </div>

        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div className="flex overflow-x-auto pb-4">
              <DroppableColumn id="library" title="Library" resources={packConfig.library || []} isLibrary={true} />
              {userRoles.map((role) => (
                <DroppableColumn key={role} id={role} title={role} resources={packConfig[role] || []} />
              ))}
            </div>
            <DragOverlay>
              {activeResource ? <DraggableResourceItem resource={activeResource} isOverlay /> : null}
            </DragOverlay>
        </DndContext>
      </div>

      <div className="mt-8 pt-6 border-t border-slate-700/50">
        <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Your configuration is saved automatically when you make changes.</p>
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

