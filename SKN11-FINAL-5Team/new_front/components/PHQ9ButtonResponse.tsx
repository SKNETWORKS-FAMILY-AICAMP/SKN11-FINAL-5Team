// components/PHQ9ButtonResponse.tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PHQ9ButtonQuestionProps {
  question: {
    index: number;
    text: string;
    progress: string;
    options: Array<{
      value: number;
      label: string;
    }>;
  };
  onResponse: (value: number) => void;
}

export function PHQ9ButtonQuestion({ question, onResponse }: PHQ9ButtonQuestionProps) {
  const colors = [
    "bg-green-100 text-green-800 hover:bg-green-200",
    "bg-yellow-100 text-yellow-800 hover:bg-yellow-200", 
    "bg-orange-100 text-orange-800 hover:bg-orange-200",
    "bg-red-100 text-red-800 hover:bg-red-200"
  ];

  return (
    <Card className="w-full max-w-2xl mx-auto mt-4 shadow-lg border-2 border-blue-100">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardTitle className="text-lg font-semibold text-gray-800 flex items-center">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center mr-3 text-sm font-bold">
            {question.index + 1}
          </div>
          PHQ-9 질문 {question.progress}
        </CardTitle>
        <p className="text-base text-gray-700 leading-relaxed mt-2 pl-11">
          {question.text}
        </p>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-3">
          {question.options.map((option) => (
            <Button
              key={option.value}
              variant="outline"
              className={`w-full h-auto p-4 text-left justify-start whitespace-normal ${colors[option.value]} border-2 border-transparent transition-all duration-300 hover:scale-[1.02] hover:shadow-md`}
              onClick={() => onResponse(option.value)}
            >
              <div className="flex items-center w-full">
                <div className="w-10 h-10 rounded-full bg-white bg-opacity-70 text-gray-600 flex items-center justify-center mr-4 font-bold text-lg">
                  {option.value}
                </div>
                <span className="flex-1 text-sm font-medium leading-relaxed">
                  {option.label}
                </span>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}