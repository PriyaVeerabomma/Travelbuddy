import { type Message } from '@/components/ui/chat-message';

export interface Conversation {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  messages: Message[];
}

export class ChatDatabase {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = "travel-buddy-db";
  private readonly DB_VERSION = 1;
  private readonly STORE_NAME = "conversations";

  async init(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = (event) => {
        console.error("IndexedDB error:", event);
        reject(false);
      };

      request.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve(true);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          const store = db.createObjectStore(this.STORE_NAME, { keyPath: "id" });
          store.createIndex("updated_at", "updated_at", { unique: false });
        }
      };
    });
  }

  async saveConversation(conversation: Conversation): Promise<string> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], "readwrite");
      const store = transaction.objectStore(this.STORE_NAME);
      
      // Update the timestamp before saving
      conversation.updated_at = Date.now();
      
      const request = store.put(conversation);
      
      request.onsuccess = () => {
        resolve(conversation.id);
      };
      
      request.onerror = (event) => {
        console.error("Error saving conversation:", event);
        reject(event);
      };
    });
  }

  async getConversation(id: string): Promise<Conversation | null> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], "readonly");
      const store = transaction.objectStore(this.STORE_NAME);
      const request = store.get(id);
      
      request.onsuccess = () => {
        resolve(request.result || null);
      };
      
      request.onerror = (event) => {
        console.error("Error getting conversation:", event);
        reject(event);
      };
    });
  }

  async getAllConversations(): Promise<Conversation[]> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], "readonly");
      const store = transaction.objectStore(this.STORE_NAME);
      const index = store.index("updated_at");
      const request = index.openCursor(null, "prev"); // Get in reverse chronological order
      
      const conversations: Conversation[] = [];
      
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        
        if (cursor) {
          conversations.push(cursor.value);
          cursor.continue();
        } else {
          resolve(conversations);
        }
      };
      
      request.onerror = (event) => {
        console.error("Error getting all conversations:", event);
        reject(event);
      };
    });
  }

  async deleteConversation(id: string): Promise<boolean> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], "readwrite");
      const store = transaction.objectStore(this.STORE_NAME);
      const request = store.delete(id);
      
      request.onsuccess = () => {
        resolve(true);
      };
      
      request.onerror = (event) => {
        console.error("Error deleting conversation:", event);
        reject(event);
      };
    });
  }
}

// Create a singleton instance
export const chatDb = new ChatDatabase();