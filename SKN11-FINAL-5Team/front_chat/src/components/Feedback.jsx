// src/components/FeedbackModal.jsx
import React from "react";

export default function FeedbackModal({
  rating,
  setRating,
  comment,
  setComment,
  category,
  setCategory,
  onClose,
  onSubmit,
}) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h3 className="text-lg font-semibold mb-4">상세 피드백</h3>

        <div className="flex space-x-1 mb-4">
          {[1, 2, 3, 4, 5].map((num) => (
            <span
              key={num}
              onClick={() => setRating(num)}
              className={`cursor-pointer text-2xl ${
                rating >= num ? "text-yellow-400" : "text-gray-300"
              }`}
            >
              ★
            </span>
          ))}
        </div>
        
        {/* 카테고리 선택 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">관련 카테고리</label>
          <select
            className="w-full border border-gray-300 rounded-md p-2 text-sm"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="general">일반</option>
            <option value="planning">사업기획</option>
            <option value="marketing">마케팅</option>
            <option value="customer">고객관리</option>
            <option value="task">업무지원</option>
            <option value="mental">멘탈코칭</option>
          </select>
        </div>

        <textarea
          className="w-full border border-gray-300 rounded-md p-2 text-sm resize-none mb-4"
          rows={4}
          placeholder="자세한 피드백을 남겨주세요..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />

        <div className="flex justify-end space-x-2">
          <button
            className="text-gray-500 px-3 py-1 rounded hover:underline"
            onClick={onClose}
          >
            취소
          </button>
          <button
            className="bg-gray-800 text-white px-4 py-1.5 rounded hover:bg-gray-700"
            onClick={onSubmit}
          >
            피드백 전송
          </button>
        </div>
      </div>
    </div>
  );
}
