import axios from "axios"; 
const BASE_URL = "http://localhost:8002";

export async function createConversation(userId) {
  const res = await axios.post(`${BASE_URL}/api/conversations`, {
    user_id: userId,
  });
  return res.data;
}


export async function sendChatMessage({ customer_id, conversation_id, question}) {
  const res = await axios.post(`${BASE_URL}/agent/query`, {
    question,
    customer_id,
    conversation_id,
  },
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  return res.data;
}

