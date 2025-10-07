import { useEffect, useState, useRef } from 'react';
import ApiService from '../services/ApiService';

// Singleton PollManager to ensure only one polling loop per page
class PollManager {
  constructor() {
    this.subscribers = new Set();
    this.interval = null;
    this.isFetching = false;
    this.lastData = null;
    this.pollIntervalMs = 5 * 1000; // 5s for debugging (was 60s)
    console.log('PollManager created with interval:', this.pollIntervalMs);
  }

  subscribe(cb) {
    this.subscribers.add(cb);
    // Immediately deliver last data if available
    if (this.lastData) cb(this.lastData);
    if (!this.interval) this.start();
    return () => this.unsubscribe(cb);
  }

  unsubscribe(cb) {
    this.subscribers.delete(cb);
    if (this.subscribers.size === 0) this.stop();
  }

  async fetchOnce() {
    if (this.isFetching) return;
    this.isFetching = true;
    console.log('PollManager: fetching usage status...');
    try {
      const res = await ApiService.getUsageStatus();
      console.log('PollManager: API response:', res);
      if (res && res.success) {
        this.lastData = res.data;
        console.log('PollManager: updating subscribers with data:', res.data);
        this.subscribers.forEach((cb) => cb(res.data));
      } else {
        console.warn('PollManager: API call unsuccessful:', res);
      }
    } catch (e) {
      console.error('PollManager fetch error', e);
    } finally {
      this.isFetching = false;
    }
  }

  start() {
    if (this.interval) return;
    
    // Register global refresh callback
    window.__AURA_USAGE_REFRESH_CALLBACK__ = (data) => {
      this.lastData = data;
      this.subscribers.forEach((cb) => cb(data));
    };
    
    // initial immediate fetch
    this.fetchOnce();
    this.interval = setInterval(() => this.fetchOnce(), this.pollIntervalMs);
    // defensive: keep a ref to interval so HMR can clear
    window.__AURA_POLL_MANAGER_INTERVAL__ = this.interval;
    console.debug('PollManager started');
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      delete window.__AURA_POLL_MANAGER_INTERVAL__;
      delete window.__AURA_USAGE_REFRESH_CALLBACK__;
      console.debug('PollManager stopped');
    }
  }

  // Expose manual refresh for UI
  refresh() {
    this.fetchOnce();
  }
}

const singleton = new PollManager();

export default function useUsageStatus() {
  const [state, setState] = useState(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    const unsub = singleton.subscribe((data) => {
      if (mounted.current) setState(data);
    });
    return () => {
      mounted.current = false;
      unsub();
    };
  }, []);

  return {
    usage: state,
    refresh: () => singleton.refresh(),
  };
}
