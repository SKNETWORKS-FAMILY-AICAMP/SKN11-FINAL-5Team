// lib/api.ts
import axios from "axios"
import {
  DashboardData,
  UsersData,
  SubscriptionAnalytics,
  FeedbackAnalytics,
} from "./data"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

export const fetchDashboardData = async (): Promise<DashboardData> => {
  const res = await axios.get(`${BASE_URL}/admin/dashboard`)
  return res.data
}

export const fetchUsersData = async (): Promise<UsersData> => {
  const res = await axios.get(`${BASE_URL}/admin/users`)
  return res.data
}

export const fetchSubscriptionData = async (): Promise<SubscriptionAnalytics> => {
  const res = await axios.get(`${BASE_URL}/admin/subscription`)
  return res.data
}

export const fetchFeedbackData = async (): Promise<FeedbackAnalytics> => {
  const res = await axios.get(`${BASE_URL}/admin/feedback`)
  return res.data
}
