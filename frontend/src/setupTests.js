// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom exposes scrollTo but intentionally does not implement its browser
// behavior; keep route-change tests focused on rendered output.
window.scrollTo = jest.fn();
