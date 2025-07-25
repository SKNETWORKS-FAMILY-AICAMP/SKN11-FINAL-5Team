export const AGENT_PORT_MAP = {
  unified_agent: 8080,
  planner: 8001,
  crm: 8002,
  marketing: 8003,
  mentalcare: 8004,
  task: 8005,
};

export const getAgentPort = (type) => AGENT_PORT_MAP[type] || AGENT_PORT_MAP["unified_agent"];