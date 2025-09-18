// FILE: frontend/components/profile/WelcomePackManager.tsx (NEW FILE)

'use client';

import { useState, useEffect, FC } from 'react';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, arrayMove } from '@dnd-kit/sortable';
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

const DraggableResourceItem: FC<{ resource: ContentResource; index: number }> = ({ resource, index }) => {
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
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className={`p-2 mb-2 bg-gray-700 border border-gray-600 rounded-md flex items-center gap-2 cursor-grab active:cursor-grabbing ${isDragging ? 'shadow-lg ring-2 ring-cyan-500 opacity-50' : ''}`}
        >
            <GripVertical className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-white truncate">{resource.title}</span>
        </div>
    );
};

const DroppableColumn: FC<{ 
    id: string; 
    title: string; 
    resources: ContentResource[]; 
    isOver?: boolean;
}> = ({ id, title, resources, isOver }) => {
    return (
        <div className={`p-3 bg-black/20 rounded-lg min-h-[200px] ${isOver ? 'ring-2 ring-cyan-500' : ''}`}>
            <h4 className="font-bold text-white mb-2 capitalize">{title}</h4>
            <SortableContext items={resources.map(r => r.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-2">
                    {resources.map((resource, index) => (
                        <DraggableResourceItem key={resource.id} resource={resource} index={index} />
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

    useEffect(() => {
        const fetchConfig = async () => {
            setIsLoading(true);
            try {
                const { config, message } = await api.get('/api/content-resources/welcome-packs-config');
                const newPackConfig: PackConfig = { library: [] };
                userRoles.forEach(role => newPackConfig[role] = []);

                const assignedIds = new Set<string>();

                Object.entries(config).forEach(([role, idList]: [string, string[]]) => {
                    if (newPackConfig[role]) {
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

        if (allResources.length > 0) {
            fetchConfig();
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

        // Find which column the active item is in
        let sourceColumn = '';
        let sourceIndex = -1;
        
        for (const [columnId, resources] of Object.entries(packConfig)) {
            const index = resources.findIndex(r => r.id === activeId);
            if (index !== -1) {
                sourceColumn = columnId;
                sourceIndex = index;
                break;
            }
        }

        if (sourceColumn === '') return;

        // Check if we're dropping on a column or another item
        const isOverColumn = Object.keys(packConfig).includes(overId);
        let targetColumn = isOverColumn ? overId : sourceColumn;
        
        // If dropping on another item, find which column it's in
        if (!isOverColumn) {
            for (const [columnId, resources] of Object.entries(packConfig)) {
                const index = resources.findIndex(r => r.id === overId);
                if (index !== -1) {
                    targetColumn = columnId;
                    break;
                }
            }
        }

        if (sourceColumn === targetColumn) {
            // Reordering within the same column
            const newConfig = { ...packConfig };
            const targetIndex = isOverColumn ? newConfig[targetColumn].length : 
                newConfig[targetColumn].findIndex(r => r.id === overId);
            
            newConfig[sourceColumn] = arrayMove(newConfig[sourceColumn], sourceIndex, targetIndex);
            setPackConfig(newConfig);
        } else {
            // Moving between columns
            const newConfig = { ...packConfig };
            const [movedItem] = newConfig[sourceColumn].splice(sourceIndex, 1);
            
            const targetIndex = isOverColumn ? newConfig[targetColumn].length : 
                newConfig[targetColumn].findIndex(r => r.id === overId);
            
            newConfig[targetColumn].splice(targetIndex, 0, movedItem);
            setPackConfig(newConfig);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setStatus('idle');
        const payload = {
            message: welcomeMessage,
            config: Object.fromEntries(
                Object.entries(packConfig)
                    .filter(([key]) => key !== 'library')
                    .map(([role, resources]) => [role.toLowerCase(), resources.map(r => r.id)])
            ),
        };

        try {
            await api.put('/api/content-resources/welcome-packs-config', payload);
            setStatus('success');
        } catch (error) {
            setStatus('error');
            console.error("Failed to save welcome pack config", error);
        } finally {
            setIsSaving(false);
            setTimeout(() => setStatus('idle'), 3000);
        }
    };

    if (isLoading) return <div className="p-6 text-center"><Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" /></div>;

    return (
        <div className="p-6">
            <div className="mb-6">
                <label htmlFor="welcomeMessage" className="block text-sm font-medium text-gray-300 mb-2">Personal Welcome Message</label>
                <Textarea
                    id="welcomeMessage"
                    placeholder="e.g., Welcome to my practice! Here are a few resources to help you get started..."
                    value={welcomeMessage}
                    onChange={(e) => setWelcomeMessage(e.target.value)}
                    className="max-w-xl"
                />
            </div>

            <DndContext
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
            >
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Library Column */}
                    <DroppableColumn
                        id="library"
                        title="Content Library"
                        resources={packConfig.library || []}
                    />

                    {/* Role Columns */}
                    {userRoles.map(role => (
                        <DroppableColumn
                            key={role}
                            id={role}
                            title={role}
                            resources={packConfig[role] || []}
                        />
                    ))}
                </div>

                <DragOverlay>
                    {activeId ? (
                        <div className="p-2 bg-gray-600 border border-gray-500 rounded-md flex items-center gap-2 shadow-lg">
                            <GripVertical className="w-4 h-4 text-gray-300" />
                            <span className="text-sm text-white">
                                {allResources.find(r => r.id === activeId)?.title}
                            </span>
                        </div>
                    ) : null}
                </DragOverlay>
            </DndContext>

            <div className="mt-6 flex justify-end items-center gap-4">
                <div className="h-5">
                    {status === 'success' && <div className="flex items-center gap-2 text-sm text-green-400"><CheckCircle size={16} /> Saved!</div>}
                    {status === 'error' && <div className="flex items-center gap-2 text-sm text-red-400"><AlertTriangle size={16} /> Error saving.</div>}
                </div>
                <Button onClick={handleSave} disabled={isSaving}>
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                    Save Welcome Packs
                </Button>
            </div>
        </div>
    );
};
