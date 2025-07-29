import axios from "axios"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005"

export const createEmailTemplate = async (userId: number, data: {
  title: string
  content: string
  channel_type: string
  content_type: string
  template_type: string 
}) => {
  const res = await axios.post(`${BASE_URL}/workspace/email`, {
    ...data,
    user_id: userId,
  })
  return res.data
}

export const updateEmailTemplate = async (templateId: number, data: {
  title: string
  content: string
  content_type: string
}) => {
  const res = await axios.put(`${BASE_URL}/workspace/email/${templateId}`, data)
  return res.data
}

// // ✅ 관리자 템플릿 + 사용자 콘텐츠 둘 다 가져오기
// export const fetchEmailTemplates = async (userId: number) => {
//   const res = await axios.get(`${BASE_URL}/workspace/email`, {
//     params: { user_id: userId },
//   })

//   return {
//     templates: res.data.email_templates,
//     contents: res.data.email_contents,
//   }
// }
