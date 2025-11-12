import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Sparkles, Music, Waves, Gamepad2, Code2, Bot, Cpu, Search } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import type { TaskTemplate } from '@/types';

interface WizardStepTemplateProps {
  onTemplateSelect: (template: TaskTemplate | null) => void;
  selectedTemplate?: TaskTemplate | null;
}

// Icon mapping based on keywords in template name/description/category
const getTemplateIcon = (template: TaskTemplate) => {
  const iconMappings = [
    { keywords: ['concert', 'ticket', 'music', 'event'], icon: Music },
    { keywords: ['swimming', 'pool', 'summer', 'seasonal'], icon: Waves },
    { keywords: ['ps5', 'playstation', 'stock', 'gaming'], icon: Gamepad2 },
    { keywords: ['framework', 'react', 'code', 'software'], icon: Code2 },
    { keywords: ['ai', 'gpt', 'model', 'robot', 'claude'], icon: Bot },
    { keywords: ['gpu', 'graphics', 'cpu', 'nvidia', 'hardware'], icon: Cpu },
  ];

  const searchText = `${template.name} ${template.description} ${template.category}`.toLowerCase();

  for (const mapping of iconMappings) {
    if (mapping.keywords.some((keyword) => searchText.includes(keyword))) {
      return mapping.icon;
    }
  }

  return Search;
};

export const WizardStepTemplate: React.FC<WizardStepTemplateProps> = ({
  onTemplateSelect,
  selectedTemplate,
}) => {
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const loadTemplates = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // Get unique categories
  const categories = Array.from(new Set(templates.map((t) => t.category))).sort();

  // Filter templates by category
  const filteredTemplates =
    selectedCategory === 'all'
      ? templates
      : templates.filter((t) => t.category === selectedCategory);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Choose Your Starting Point</h2>
        <p className="text-muted-foreground">
          Select a template to get started quickly, or create from scratch
        </p>
      </div>

      {/* Category Tabs */}
      {categories.length > 0 && (
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="w-full justify-start overflow-x-auto">
            <TabsTrigger value="all">All Templates</TabsTrigger>
            {categories.map((category) => (
              <TabsTrigger key={category} value={category}>
                {category}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      )}

      {/* Template Grid */}
      {filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTemplates.map((template) => {
            const Icon = getTemplateIcon(template);
            const isSelected = selectedTemplate?.id === template.id;

            return (
              <Card
                key={template.id}
                className={`cursor-pointer hover:border-primary transition-all group relative overflow-hidden ${
                  isSelected ? 'border-primary ring-2 ring-primary/20' : ''
                }`}
                onClick={() => onTemplateSelect(template)}
              >
                {/* Gradient overlay on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                <CardContent className="p-6 relative">
                  {/* Icon */}
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>

                  {/* Title */}
                  <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">
                    {template.name}
                  </h3>

                  {/* Description */}
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {template.description}
                  </p>

                  {/* Category Badge */}
                  <Badge variant="outline" className="text-xs">
                    {template.category}
                  </Badge>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No templates found in this category</p>
        </div>
      )}

      {/* Start from Scratch */}
      <div className="mt-8 relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-muted" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-background px-4 text-sm text-muted-foreground">or</span>
        </div>
      </div>

      <Button
        variant="outline"
        size="lg"
        className="w-full"
        onClick={() => onTemplateSelect(null)}
      >
        <Sparkles className="mr-2 h-4 w-4" />
        Start from Scratch
      </Button>
    </div>
  );
};
