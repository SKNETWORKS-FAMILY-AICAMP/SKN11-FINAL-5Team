// src/workspace/components/TemplateEditor.tsx
"use client"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

interface Props {
  form: {
    title: string
    content: string
    tags: string
  }
  onChange: (form: { title: string; content: string; tags: string }) => void
}

export default function TemplateEditor({ form, onChange }: Props) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="contentTitle" className="text-sm">
          제목
        </Label>
        <Input
          id="contentTitle"
          placeholder="콘텐츠 제목을 입력하세요"
          value={form.title}
          onChange={(e) => onChange({ ...form, title: e.target.value })}
          className="rounded-lg"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="contentBody" className="text-sm">
          내용
        </Label>
        <Textarea
          id="contentBody"
          placeholder="콘텐츠 내용을 입력하세요..."
          className="min-h-[300px] rounded-lg"
          value={form.content}
          onChange={(e) => onChange({ ...form, content: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="contentTags" className="text-sm">
          태그
        </Label>
        <Input
          id="contentTags"
          placeholder="태그를 쉼표로 구분하여 입력하세요"
          value={form.tags}
          onChange={(e) => onChange({ ...form, tags: e.target.value })}
          className="rounded-lg"
        />
      </div>
    </>
  )
}
