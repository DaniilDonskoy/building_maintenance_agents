export interface Task {
    agent: string;
    time: string;
    task: string;
    node: string;
    cost: number;
}

export interface TableData {
    tasks: Task[];
}