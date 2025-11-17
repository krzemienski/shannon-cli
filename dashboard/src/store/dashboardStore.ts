import { create } from 'zustand';
import type { DashboardState, ExecutionState, Skill, FileChange, Event, Agent } from '../types';

interface DashboardStore extends DashboardState {
  // Actions
  setConnected: (connected: boolean) => void;
  addEvent: (event: Event) => void;
  clearEvents: () => void;
  updateExecution: (updates: Partial<ExecutionState>) => void;
  updateSkill: (skillId: string, updates: Partial<Skill>) => void;
  addSkill: (skill: Skill) => void;
  removeSkill: (skillId: string) => void;
  updateFile: (filePath: string, updates: Partial<FileChange>) => void;
  addFile: (file: FileChange) => void;
  removeFile: (filePath: string) => void;
  processEvent: (event: Event) => void;
}

const initialExecutionState: ExecutionState = {
  taskName: 'No task running',
  status: 'idle',
  progress: 0,
  startTime: null,
  elapsedTime: 0,
  estimatedTimeRemaining: null,
};

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  execution: initialExecutionState,
  skills: [],
  files: [],
  events: [],
  connected: false,
  agents: [],
  agentStats: {
    totalAgents: 0,
    activeAgents: 0,
    idleAgents: 0,
    maxActive: 10,
    maxTotal: 20,
    queuedTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    totalProcessed: 0,
    poolUptime: 0,
  },
  pendingDecisions: [],
  resolvedDecisions: [],
  validationResults: [],
  isValidating: false,
  validationOutput: [],

  setConnected: (connected) => set({ connected }),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event],
    })),

  clearEvents: () => set({ events: [] }),

  updateExecution: (updates) =>
    set((state) => ({
      execution: { ...state.execution, ...updates },
    })),

  updateSkill: (skillId, updates) =>
    set((state) => ({
      skills: state.skills.map((skill) =>
        skill.id === skillId ? { ...skill, ...updates } : skill
      ),
    })),

  addSkill: (skill) =>
    set((state) => ({
      skills: [...state.skills, skill],
    })),

  removeSkill: (skillId) =>
    set((state) => ({
      skills: state.skills.filter((s) => s.id !== skillId),
    })),

  updateFile: (filePath, updates) =>
    set((state) => ({
      files: state.files.map((file) =>
        file.path === filePath ? { ...file, ...updates } : file
      ),
    })),

  addFile: (file) =>
    set((state) => ({
      files: [...state.files, file],
    })),

  removeFile: (filePath) =>
    set((state) => ({
      files: state.files.filter((f) => f.path !== filePath),
    })),

  // Process incoming events and update state
  processEvent: (event) => {
    const { type, data } = event;

    // Add event to history
    get().addEvent(event);

    // Update state based on event type
    switch (type) {
      case 'execution_started':
        get().updateExecution({
          taskName: data.task_name || 'Task running',
          status: 'running',
          progress: 0,
          startTime: Date.now(),
          elapsedTime: 0,
        });
        break;

      case 'execution_paused':
        get().updateExecution({
          status: 'paused',
        });
        break;

      case 'execution_resumed':
        get().updateExecution({
          status: 'running',
        });
        break;

      case 'execution_completed':
        get().updateExecution({
          status: 'completed',
          progress: 100,
        });
        break;

      case 'execution_failed':
        get().updateExecution({
          status: 'failed',
        });
        break;

      case 'execution_progress':
        get().updateExecution({
          progress: data.progress || 0,
          elapsedTime: data.elapsed_time || 0,
          estimatedTimeRemaining: data.estimated_time_remaining || null,
        });
        break;

      case 'skill_started':
        if (data.skill_id && data.skill_name) {
          const existingSkill = get().skills.find((s) => s.id === data.skill_id);
          if (existingSkill) {
            get().updateSkill(data.skill_id, {
              status: 'running',
              startTime: Date.now(),
            });
          } else {
            get().addSkill({
              id: data.skill_id,
              name: data.skill_name,
              status: 'running',
              progress: 0,
              duration: 0,
              startTime: Date.now(),
              endTime: null,
            });
          }
        }
        break;

      case 'skill_completed':
        if (data.skill_id) {
          const skill = get().skills.find((s) => s.id === data.skill_id);
          get().updateSkill(data.skill_id, {
            status: 'completed',
            progress: 100,
            endTime: Date.now(),
            duration: skill?.startTime ? Date.now() - skill.startTime : 0,
          });
        }
        break;

      case 'skill_failed':
        if (data.skill_id) {
          const skill = get().skills.find((s) => s.id === data.skill_id);
          get().updateSkill(data.skill_id, {
            status: 'failed',
            endTime: Date.now(),
            duration: skill?.startTime ? Date.now() - skill.startTime : 0,
          });
        }
        break;

      case 'skill_progress':
        if (data.skill_id) {
          get().updateSkill(data.skill_id, {
            progress: data.progress || 0,
          });
        }
        break;

      case 'file_changed':
        if (data.file_path) {
          const existingFile = get().files.find((f) => f.path === data.file_path);
          if (existingFile) {
            get().updateFile(data.file_path, {
              status: data.status || 'modified',
              diff: data.diff || existingFile.diff,
            });
          } else {
            get().addFile({
              path: data.file_path,
              status: data.status || 'modified',
              diff: data.diff || '',
              approved: false,
            });
          }
        }
        break;

      case 'file_approved':
        if (data.file_path) {
          get().updateFile(data.file_path, {
            approved: true,
          });
        }
        break;

      case 'file_reverted':
        if (data.file_path) {
          get().removeFile(data.file_path);
        }
        break;

      case 'execution_state':
        // Response to get_execution_state command
        if (data) {
          get().updateExecution({
            taskName: data.task_name || get().execution.taskName,
            status: data.status || get().execution.status,
            progress: data.progress !== undefined ? data.progress : get().execution.progress,
            startTime: data.start_time || get().execution.startTime,
            elapsedTime: data.elapsed_time || get().execution.elapsedTime,
            estimatedTimeRemaining: data.estimated_time_remaining !== undefined
              ? data.estimated_time_remaining
              : get().execution.estimatedTimeRemaining,
          });
        }
        break;

      case 'skill_status':
        // Response to get_skill_status command
        if (data.skills && Array.isArray(data.skills)) {
          data.skills.forEach((skillData: any) => {
            const existingSkill = get().skills.find((s) => s.id === skillData.skill_id);
            if (existingSkill) {
              get().updateSkill(skillData.skill_id, {
                name: skillData.skill_name || existingSkill.name,
                status: skillData.status || existingSkill.status,
                progress: skillData.progress !== undefined ? skillData.progress : existingSkill.progress,
              });
            } else {
              get().addSkill({
                id: skillData.skill_id,
                name: skillData.skill_name || 'Unknown Skill',
                status: skillData.status || 'pending',
                progress: skillData.progress || 0,
                duration: 0,
                startTime: null,
                endTime: null,
              });
            }
          });
        }
        break;

      // Agent pool events
      case 'agent:spawned':
        if (data.data && data.data.agent_id) {
          const newAgent: Agent = {
            agentId: data.data.agent_id,
            role: data.data.role || 'generic',
            status: 'active',
            currentTask: data.data.skill_name || null,
            tasksCompleted: 0,
            tasksFailed: 0,
            totalTime: 0,
            lastActive: new Date().toISOString()
          };
          set((state) => ({
            agents: [...state.agents, newAgent],
            agentStats: {
              ...state.agentStats,
              totalAgents: state.agents.length + 1,
              activeAgents: state.agents.filter(a => a.status === 'active').length + 1
            }
          }));
        }
        break;

      case 'agent:completed':
        if (data.data && data.data.agent_id) {
          set((state) => ({
            agents: state.agents.map(a =>
              a.agentId === data.data.agent_id
                ? {
                    ...a,
                    status: data.data.success ? 'completed' : 'failed',
                    currentTask: null,
                    tasksCompleted: data.data.success ? a.tasksCompleted + 1 : a.tasksCompleted,
                    tasksFailed: !data.data.success ? a.tasksFailed + 1 : a.tasksFailed,
                    totalTime: a.totalTime + (data.data.duration || 0)
                  }
                : a
            ),
            agentStats: {
              ...state.agentStats,
              activeAgents: state.agents.filter(a => a.status === 'active').length - 1,
              completedTasks: data.data.success
                ? state.agentStats.completedTasks + 1
                : state.agentStats.completedTasks,
              failedTasks: !data.data.success
                ? state.agentStats.failedTasks + 1
                : state.agentStats.failedTasks
            }
          }));
        }
        break;

      case 'agent:progress':
        if (data.data && data.data.agent_id) {
          set((state) => ({
            agents: state.agents.map(a =>
              a.agentId === data.data.agent_id
                ? { ...a, lastActive: new Date().toISOString() }
                : a
            )
          }));
        }
        break;

      // Handle colon-separated event types from new client-server architecture
      case 'execution:started':
        // Data is nested: {timestamp, data: {task, plan_id, ...}, session_id}
        if (data.data && data.data.task) {
          get().updateExecution({
            taskName: data.data.task,
            status: 'running',
            startTime: Date.now(),
            progress: 0,
          });
        }
        break;

      case 'execution:completed':
        get().updateExecution({
          status: 'completed',
          progress: 100,
          elapsedTime: Date.now() - (get().execution.startTime || Date.now()),
        });
        break;

      case 'execution:failed':
        get().updateExecution({
          status: 'failed',
        });
        break;

      case 'skill:started':
        // Colon version of skill_started
        // Data is nested: {timestamp, data: {skill_name, step_index, ...}, session_id}
        if (data.data && data.data.skill_name) {
          const skillId = `${data.data.skill_name}_${data.data.step_index || Date.now()}`;
          get().addSkill({
            id: skillId,
            name: data.data.skill_name,
            status: 'running',
            progress: 0,
            duration: 0,
            startTime: Date.now(),
            endTime: null,
          });
        }
        break;

      case 'skill:completed':
        // Colon version of skill_completed
        // Data is nested: {timestamp, data: {skill_name, duration, ...}, session_id}
        if (data.data && data.data.skill_name) {
          const skills = get().skills;
          const skill = skills.find((s) => s.name === data.data.skill_name && s.status === 'running');
          if (skill) {
            get().updateSkill(skill.id, {
              status: 'completed',
              progress: 100,
              endTime: Date.now(),
              duration: data.data.duration ? data.data.duration * 1000 : (Date.now() - (skill.startTime || Date.now())),
            });
          }
        }
        break;

      case 'checkpoint:created':
        // Just acknowledge - could add checkpoint tracking later
        if (data.data) {
          console.log('Checkpoint created:', data.data.checkpoint_id);
        }
        break;

      case 'validation:started':
        set({ isValidating: true, validationOutput: [] });
        break;

      case 'validation:output':
        if (data.data && data.data.line) {
          set((state) => ({
            validationOutput: [
              ...state.validationOutput,
              {
                line: data.data.line,
                type: data.data.type || 'stdout',
                checkName: data.data.check_name || 'validation',
                timestamp: data.data.timestamp || Date.now(),
              },
            ],
          }));
        }
        break;

      case 'validation:completed':
        set({ isValidating: false });
        if (data.data) {
          console.log('Validation completed:', data.data.check_name, data.data.success ? 'PASS' : 'FAIL');
        }
        break;

      // Server connection events
      case 'connected':
        // Server connected, log but don't update execution state
        console.log('Server connected:', data);
        break;

      case 'command:result':
        // Command response from server, log but don't update UI
        console.log('Command result:', data);
        break;

      default:
        // Unknown event type - just log it
        console.log('Unknown event type:', type);
    }
  },
}));
