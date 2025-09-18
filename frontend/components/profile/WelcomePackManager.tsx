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
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Loader2, Save, AlertTriangle, CheckCircle } from 'lucide-react';
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
const DraggableResourceItem: FC<{ resource: ContentResource }> = ({ resource }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ 
    id: resource.id 
  });
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`p-2 mb-2 bg-gray-700 border border-gray-600 rounded-md flex items-center gap-2 cursor-grab active:cursor-grabbing ${
        isDragging ? 'shadow-lg ring-2 ring-cyan-500' : ''
      }`}
    >
      <GripVertical className="w-4 h-4 text-gray-500" />
      <span className="text-sm text-white truncate">{resource.title}</span>
    </div>
  );
};

// Fixed DroppableColumn with useDroppable hook
const DroppableColumn: FC<{
  title: string;
  resources: ContentResource[];
  containerId: string;
}> = ({ title, resources, containerId }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: containerId,
  });

  return (
    <div 
      ref={setNodeRef}
      className={`p-3 bg-black/20 rounded-lg transition-colors ${
        isOver ? 'bg-cyan-500/20 ring-2 ring-cyan-500' : ''
      }`}
    >
      <h4 className="font-bold text-white mb-2 capitalize">{title}</h4>
      <SortableContext items={resources.map(r => r.id)} strategy={verticalListSortingStrategy}>
        <div className="min-h-[200px] space-y-2">
          {resources.map((resource) => (
            <DraggableResourceItem key={resource.id} resource={resource} />
          ))}
        </div>
      </SortableContext>
    </div>
  );
};

export const WelcomePackManager: FC<WelcomePackManagerProps> = ({ api, allResources, userRoles }) => {
  const [packConfig, setPackConfig] = useState<PackConfig>({});
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  useEffect(() => {
    const fetchConfig = async () => {
      setIsLoading(true);
      try {
        const { config, message } = await api.get('/api/content-resources/welcome-packs-config');
        const newPackConfig: PackConfig = { library: [] };
        userRoles.forEach(role => newPackConfig[role] = []);
        const assignedIds = new Set<string>();

        Object.entries(config).forEach(([role, idList]: [string, any]) => {
          if (newPackConfig[role] && Array.isArray(idList)) {
            newPackConfig[role] = idList.map(id => allResources.find(r => r.id === id)).filter(Boolean) as ContentResource[];
            idList.forEach(id => assignedIds.add(id));
          }
        });

        newPackConfig.library = allResources.filter(r => !assignedIds.has(r.id));
        setPackConfig(newPackConfig);
        setWelcomeMessage(message || '');
      } catch (error) {
        console.error("Failed to fetch welcome pack config", error);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (allResources.length > 0 && userRoles.length > 0) {
      fetchConfig();
    }
  }, [api, allResources, userRoles]);

  const findContainer = (id: string) => {
    return Object.keys(packConfig).find(key => 
      packConfig[key]?.some(item => item.id === id)
    );
  };

  const handleDragStart = (event: any) => setActiveId(event.active.id);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const sourceContainer = findContainer(active.id as string);
    const destContainer = findContainer(over.id as string) || (packConfig[over.id as string] ? over.id as string : null);

    if (!sourceContainer || !destContainer) return;

    setPackConfig(prev => {
      const newConfig = { ...prev };
      const sourceItems = [...newConfig[sourceContainer]];
      const activeIndex = sourceItems.findIndex(item => item.id === active.id);
      const [movedItem] = sourceItems.splice(activeIndex, 1);

      if (sourceContainer === destContainer) {
        const overIndex = sourceItems.findIndex(item => item.id === over.id);
        sourceItems.splice(overIndex, 0, movedItem);
        newConfig[sourceContainer] = sourceItems;
      } else {
        const destItems = [...newConfig[destContainer]];
        const overIndex = destItems.findIndex(item => item.id === over.id);

        if (sourceContainer === 'library') {
          // COPY logic: don't remove from library
          if (!destItems.some(item => item.id === movedItem.id)) {
            destItems.splice(overIndex !== -1 ? overIndex : destItems.length, 0, movedItem);
          }
          newConfig[destContainer] = destItems;
        } else {
          // MOVE logic: remove from source
          destItems.splice(overIndex !== -1 ? overIndex : destItems.length, 0, movedItem);
          newConfig[sourceContainer] = sourceItems;
          newConfig[destContainer] = destItems;
        }
      }
      return newConfig;
    });
  };

    const handleDragOver = (event: DragEndEvent) => {
        // This function can be used for visual feedback during drag, but the state mutation is handled in onDragEnd.
        // For now, we leave it empty to prevent the previous bug.
    };

    const handleDragEnd_OLD = (event: DragEndEvent) => {
      const { active, over } = event;
      setActiveId(null);
      if (!over) return;

      const activeContainer = findContainer(active.id as string);
      const overContainerId = packConfig[over.id as string] ? (over.id as string) : findContainer(over.id as string);

      if (!activeContainer || !overContainerId || !packConfig[activeContainer]) return;

      if (activeContainer === overContainerId) {
        setPackConfig(prev => {
          const newConfig = { ...prev };
          const items = [...newConfig[activeContainer]];
          const activeIndex = items.findIndex(item => item.id === active.id);
          const overIndex = items.findIndex(item => item.id === over.id);

          if (activeIndex !== -1 && overIndex !== -1 && activeIndex !== overIndex) {
            newConfig[activeContainer] = arrayMove(items, activeIndex, overIndex);
          }

          return newConfig;
        });
      }
    };

  const handleSave = async () => {
    setIsSaving(true);
    setStatus('idle');
    
    // Ensure payload structure matches backend expectations
    const payload = {
      message: welcomeMessage,
      config: Object.fromEntries(
        Object.entries(packConfig)
          .filter(([key]) => key !== 'library')
          .map(([role, resources]) => [
            role.toLowerCase(), 
            (resources || []).map(r => String(r.id))
          ])
      ),
    };

    // Debug logging
    console.log('Sending payload:', JSON.stringify(payload, null, 2));

    try {
      const response = await api.put('/api/content-resources/welcome-packs-config', payload);
      console.log('Save successful:', response);
      setStatus('success');
    } catch (error: any) {
      console.error('Save failed:');
      console.error('Error:', error);
      console.error('Response:', error.response?.data);
      console.error('Status:', error.response?.status);
      setStatus('error');
    } finally {
      setIsSaving(false);
      setTimeout(() => setStatus('idle'), 3000);
    }
  };

  const activeItem = activeId ? allResources.find(r => r.id === activeId) : null;

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <label htmlFor="welcomeMessage" className="block text-sm font-medium text-gray-300 mb-2">
          Personal Welcome Message
        </label>
        <Textarea
          id="welcomeMessage"
          placeholder="e.g., Welcome to my practice! Here are a few resources to help you get started..."
          value={welcomeMessage}
          onChange={(e) => setWelcomeMessage(e.target.value)}
          className="max-w-xl"
        />
      </div>
      
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DroppableColumn 
            title="Content Library" 
            resources={packConfig.library || []} 
            containerId="library" 
          />
          {userRoles.map(role => (
            <DroppableColumn 
              key={role} 
              title={role} 
              resources={packConfig[role] || []} 
              containerId={role} 
            />
          ))}
        </div>
        
        <DragOverlay>
          {activeItem ? (
            <div className="p-2 bg-gray-700 border border-gray-600 rounded-md flex items-center gap-2 shadow-lg ring-2 ring-cyan-500 opacity-90">
              <GripVertical className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-white truncate">{activeItem.title}</span>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
      
      <div className="mt-6 flex justify-end items-center gap-4">
        <div className="h-5">
          {status === 'success' && (
            <div className="flex items-center gap-2 text-sm text-green-400">
              <CheckCircle size={16} /> Saved!
            </div>
          )}
          {status === 'error' && (
            <div className="flex items-center gap-2 text-sm text-red-400">
              <AlertTriangle size={16} /> Error saving.
            </div>
          )}
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Welcome Packs
        </Button>
      </div>
    </div>
  );
};
