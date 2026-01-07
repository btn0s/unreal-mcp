#!/usr/bin/env npx tsx
/**
 * Generate Cursor MCP install deeplink based on current repository location
 */

import * as path from 'path';
import * as os from 'os';
import { execSync } from 'child_process';

const REPO_ROOT = process.cwd();
const SERVER_SCRIPT_PATH = path.join(REPO_ROOT, 'Python', 'unreal_mcp_server.py');
const PYTHON_DIR = path.join(REPO_ROOT, 'Python');

// Normalize path for Windows (use forward slashes for compatibility)
function normalizePath(filePath: string): string {
    return filePath.replace(/\\/g, '/');
}

// Check if a command is available
function isCommandAvailable(command: string): boolean {
    try {
        const isWindows = os.platform() === 'win32';
        const checkCommand = isWindows ? `where ${command}` : `which ${command}`;
        const result = execSync(checkCommand, { stdio: 'pipe', shell: true, encoding: 'utf-8' });
        return result.trim().length > 0;
    } catch {
        return false;
    }
}

// Detect the best available Python executable
function detectPythonCommand(): { command: string; args: string[] } {
    const normalizedPythonDir = normalizePath(PYTHON_DIR);
    const normalizedScriptPath = normalizePath(SERVER_SCRIPT_PATH);
    
    // Priority: uv > python > python3
    if (isCommandAvailable('uv')) {
        return {
            command: 'uv',
            args: [
                '--directory',
                normalizedPythonDir,
                'run',
                'unreal_mcp_server.py'
            ]
        };
    }
    
    if (isCommandAvailable('python')) {
        return {
            command: 'python',
            args: [
                '-u',
                normalizedScriptPath
            ]
        };
    }
    
    if (isCommandAvailable('python3')) {
        return {
            command: 'python3',
            args: [
                '-u',
                normalizedScriptPath
            ]
        };
    }
    
    // Fallback to python (will show error if not available, but config is valid)
    return {
        command: 'python',
        args: [
            '-u',
            normalizedScriptPath
        ]
    };
}

function generateDeeplink(): void {
    const pythonConfig = detectPythonCommand();
    
    // Construct MCP server configuration
    const mcpConfig = {
        mcpServers: {
            unrealMCP: {
                command: pythonConfig.command,
                args: pythonConfig.args
            }
        }
    };
    
    // Encode configuration as base64
    const configJson = JSON.stringify(mcpConfig, null, 2);
    const configBase64 = Buffer.from(configJson).toString('base64');
    
    // Generate deeplink
    const deeplink = `cursor://mcp/install?config=${configBase64}`;
    
    console.log('Instructions: One-click install with Cursor, or add this to your mcp.json\n');
    console.log('Deeplink:');
    console.log(deeplink);
    console.log('\nmcp.json snippet:');
    console.log(configJson);
}

generateDeeplink();

