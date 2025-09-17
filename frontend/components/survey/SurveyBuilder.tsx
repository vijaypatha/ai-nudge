// components/survey/SurveyBuilder.tsx
// Purpose: Survey builder component for creating and editing surveys
'use client';

import { useState, useEffect } from 'react';
import { SurveyTemplate } from '@/app/(main)/surveys/page';
import { Eye, Plus, Trash2, GripVertical, Save, Loader2 } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

export enum QuestionType {
    TEXT = "text",
    NUMBER = "number",
    SELECT = "select",
    MULTI_SELECT = "multi_select",
    BOOLEAN = "boolean"
}

export interface Question {
    id: string;
    template_id: string;
    question_text: string;
    question_type: QuestionType;
    options: string[] | null;
    is_required: boolean;
    placeholder: string | null;
    help_text: string | null;
    preference_key: string | null;
    display_order: number;
}

interface SurveyBuilderProps {
    template: SurveyTemplate;
    onTemplateUpdate: (updatedData: Partial<SurveyTemplate>) => void;
}

const QuestionEditor = ({ question, onSave, onDelete, onCancel, isSaving, isDeleting }: any) => {
    const [editedQuestion, setEditedQuestion] = useState(question);
    const handleSave = () => { onSave(editedQuestion); };
    const handleOptionChange = (index: number, value: string) => {
        const newOptions = [...(editedQuestion.options || [])];
        newOptions[index] = value;
        setEditedQuestion({ ...editedQuestion, options: newOptions });
    };
    const addOption = () => {
        const newOptions = [...(editedQuestion.options || []), `Option ${(editedQuestion.options?.length || 0) + 1}`];
        setEditedQuestion({ ...editedQuestion, options: newOptions });
    };
    const removeOption = (index: number) => {
        const newOptions = [...(editedQuestion.options || [])];
        newOptions.splice(index, 1);
        setEditedQuestion({ ...editedQuestion, options: newOptions });
    };
    return (
        <div className="space-y-4 p-4 bg-black/20 rounded-lg border-2 border-cyan-500/50">
            <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                    <label className="text-xs font-semibold text-gray-400">Question Text</label>
                    <input value={editedQuestion.question_text} onChange={e => setEditedQuestion({ ...editedQuestion, question_text: e.target.value })} className="w-full mt-1 bg-black/30 p-2 rounded-md border border-white/10" />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-400">Question Type</label>
                    <select value={editedQuestion.question_type} onChange={e => setEditedQuestion({ ...editedQuestion, question_type: e.target.value, options: ['select', 'multi_select'].includes(e.target.value) ? (editedQuestion.options || []) : null })} className="w-full mt-1 bg-black/30 p-2 rounded-md border border-white/10">
                        {Object.values(QuestionType).map(type => (<option key={type} value={type}>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>))}
                    </select>
                </div>
            </div>
            {(editedQuestion.question_type === 'select' || editedQuestion.question_type === 'multi_select') && (
                <div className="space-y-2 pt-2 border-t border-white/10">
                    <label className="text-xs font-semibold text-gray-400">Options</label>
                    {editedQuestion.options?.map((option: string, index: number) => (
                        <div key={index} className="flex items-center gap-2"><input value={option} onChange={(e) => handleOptionChange(index, e.target.value)} className="w-full bg-black/30 p-1.5 rounded-md border border-white/10 text-sm" /><button onClick={() => removeOption(index)} className="p-1.5 text-gray-400 hover:text-red-400"><Trash2 size={14} /></button></div>
                    ))}
                    <button onClick={addOption} className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">+ Add Option</button>
                </div>
            )}
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-white/10">
                <div>
                    <label className="text-xs font-semibold text-gray-400">Placeholder Text</label>
                    <input value={editedQuestion.placeholder || ''} onChange={e => setEditedQuestion({ ...editedQuestion, placeholder: e.target.value })} className="w-full mt-1 bg-black/30 p-2 rounded-md border border-white/10" />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-400">Help Text / Subtitle</label>
                    <input value={editedQuestion.help_text || ''} onChange={e => setEditedQuestion({ ...editedQuestion, help_text: e.target.value })} className="w-full mt-1 bg-black/30 p-2 rounded-md border border-white/10" />
                </div>
            </div>
            <div className="flex items-center justify-start pt-2">
                <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer"><input type="checkbox" checked={editedQuestion.is_required} onChange={e => setEditedQuestion({ ...editedQuestion, is_required: e.target.checked })} className="w-4 h-4 text-cyan-400 bg-black/20 border-white/10 rounded focus:ring-cyan-400" />This question is required</label>
            </div>
            <div className="flex justify-end gap-2 pt-4 border-t border-white/20">
                <button onClick={onCancel} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
                <button onClick={onDelete} disabled={isDeleting} className="px-3 py-1 text-xs font-semibold bg-red-500/20 text-red-400 rounded-md flex items-center gap-1.5">{isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 size={14} />} Delete</button>
                <button onClick={handleSave} disabled={isSaving} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md flex items-center gap-1.5">{isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save size={14} />} Save</button>
            </div>
        </div>
    );
};

export const SurveyBuilder = ({ template, onTemplateUpdate }: SurveyBuilderProps) => {
    const { api } = useAppContext();
    const [name, setName] = useState(template.name);
    const [description, setDescription] = useState(template.description || '');
    const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Debounced save for name and description now calls the parent handler
    useEffect(() => {
        const handler = setTimeout(() => {
            if (name !== template.name || description !== template.description) {
                onTemplateUpdate({ name, description });
            }
        }, 1000);
        return () => clearTimeout(handler);
    }, [name, description, template.name, template.description, onTemplateUpdate]);

    const handleAddQuestion = async () => {
        try {
            // ✅ FIX: Use `(template.questions || [])` to prevent crash on new surveys
            const currentQuestions = template.questions || [];
            const newQuestion = await api.post(`/api/surveys/templates/${template.id}/questions`, {
                question_text: 'New Question', question_type: 'text', display_order: currentQuestions.length,
            });
            onTemplateUpdate({ questions: [...currentQuestions, newQuestion] });
            setSelectedQuestionId(newQuestion.id);
        } catch (e) { console.error(e) }
    };

    const handleUpdateQuestion = async (updatedQuestion: Question) => {
        setIsSaving(true);
        try {
            const savedQuestion = await api.put(`/api/surveys/questions/${updatedQuestion.id}`, updatedQuestion);
            const newQuestions = (template.questions || []).map(q => q.id === savedQuestion.id ? savedQuestion : q);
            onTemplateUpdate({ questions: newQuestions });
            setSelectedQuestionId(null);
        } catch (e) { console.error(e) }
        finally { setIsSaving(false) }
    }

    const handleDeleteQuestion = async (questionId: string) => {
        if (!window.confirm("Are you sure?")) return;
        try {
            await api.del(`/api/surveys/questions/${questionId}`);
            const newQuestions = (template.questions || []).filter(q => q.id !== questionId);
            onTemplateUpdate({ questions: newQuestions });
            setSelectedQuestionId(null);
        } catch (e) { console.error(e) }
    }

    const sensors = useSensors(useSensor(PointerSensor));

    const handleDragEnd = async (event: any) => {
        const { active, over } = event;
        if (active.id !== over.id) {
            const currentQuestions = template.questions || [];
            const oldIndex = currentQuestions.findIndex(q => q.id === active.id);
            const newIndex = currentQuestions.findIndex(q => q.id === over.id);
            const reorderedQuestions = arrayMove(currentQuestions, oldIndex, newIndex);
            const updatedQuestionsForApi = reorderedQuestions.map((q, index) => ({ id: q.id, display_order: index }));

            onTemplateUpdate({ questions: reorderedQuestions.map((q, index) => ({ ...q, display_order: index })) });

            try {
                await api.post('/api/surveys/questions/reorder', updatedQuestionsForApi);
            } catch (error) {
                console.error("Failed to reorder questions:", error);
                onTemplateUpdate({ questions: template.questions });
                alert("Failed to save new question order.");
            }
        }
    };

    const SortableQuestionItem = ({ question, index, isSelected, onSelect }: any) => {
        const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: question.id });
        const style = { transform: CSS.Transform.toString(transform), transition, };
        return (<div ref={setNodeRef} style={style} {...attributes} > <div onClick={() => onSelect(question.id)} className={`p-4 border-2 rounded-lg cursor-pointer flex items-start gap-4 ${isSelected ? 'border-cyan-400/50 bg-white/10' : 'border-transparent bg-white/5 hover:border-cyan-400/50'}`}> <button {...listeners} className="cursor-grab active:cursor-grabbing"><GripVertical className="h-5 w-5 text-gray-500 mt-0.5 flex-shrink-0" /></button> <div className="flex-grow"> <p className="font-semibold text-white">{index + 1}. {question.question_text} {question.is_required && <span className="text-red-400">*</span>}</p> <p className="text-xs text-gray-500 mt-1 uppercase">{question.question_type.replace(/_/g, ' ')}</p> </div> </div> </div>);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
            <div className="lg:col-span-1 bg-brand-primary border border-white/10 rounded-xl p-5 flex flex-col">
                <div>
                    <h2 className="font-bold text-xl mb-4">Survey Editor</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-semibold text-gray-400">Survey Name</label>
                            <input value={name} onChange={e => setName(e.target.value)} className="w-full mt-1 bg-black/20 p-2 rounded-lg border border-white/10" />
                        </div>
                        <div>
                            <label className="text-sm font-semibold text-gray-400">Description</label>
                            <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full mt-1 bg-black/20 p-2 rounded-lg border border-white/10" rows={3}></textarea>
                        </div>
                    </div>
                </div>
            </div>
            {/* Right Panel: Live Preview */}
            <div className="lg:col-span-2 bg-brand-primary border border-white/10 rounded-xl p-5 flex flex-col h-full">
                {/* Header (remains fixed at the top) */}
                <div className="flex justify-between items-center mb-6 flex-shrink-0">
                    <h2 className="font-bold text-xl">Live Preview</h2>
                    <div className="flex items-center gap-2 text-sm text-gray-400"><Eye size={16} /> Client View</div>
                </div>

                {/* ✅ FIX: This div is now the scrollable container */}
                <div className="flex-grow space-y-3 overflow-y-auto min-h-0 pr-2">
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                        <SortableContext items={(template.questions || []).map(q => q.id)} strategy={verticalListSortingStrategy}>
                            {(template.questions || []).sort((a, b) => a.display_order - b.display_order).map((q, index) => (
                                selectedQuestionId === q.id ? (
                                    <QuestionEditor key={q.id} question={q} onSave={handleUpdateQuestion} onDelete={() => handleDeleteQuestion(q.id)} onCancel={() => setSelectedQuestionId(null)} isSaving={isSaving} />
                                ) : (
                                    <SortableQuestionItem key={q.id} question={q} index={index} isSelected={selectedQuestionId === q.id} onSelect={setSelectedQuestionId} />
                                )
                            ))}
                        </SortableContext>
                    </DndContext>
                </div>

                {/* Footer Button (remains fixed at the bottom) */}
                <button onClick={handleAddQuestion} className="w-full mt-6 py-3 border-2 border-dashed border-white/20 rounded-lg text-sm font-semibold text-gray-400 hover:bg-white/5 hover:text-white transition-colors flex-shrink-0">
                    <Plus size={16} className="inline-block mr-2" /> Add Question
                </button>
            </div>
        </div>
    );
};