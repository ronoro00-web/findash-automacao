import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
    getFunctions,
    httpsCallable
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-functions.js";
import { firebaseConfig } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
const functions = getFunctions(app);

const googleProvider = new GoogleAuthProvider();

export function watchAuth(callback) {
    return onAuthStateChanged(auth, callback);
}

export function signInGoogle() {
    return signInWithPopup(auth, googleProvider);
}

export function signUpEmail(email, password) {
    return createUserWithEmailAndPassword(auth, email, password);
}

export function signInEmail(email, password) {
    return signInWithEmailAndPassword(auth, email, password);
}

export function signOutUser() {
    return signOut(auth);
}

const callNews = httpsCallable(functions, 'get_asset_news');
const callTechnical = httpsCallable(functions, 'get_technical_analysis');
const callFundamental = httpsCallable(functions, 'get_fundamental_analysis');

export async function fetchAssetNews(ticker) {
    const res = await callNews({ ticker });
    return res.data;
}

export async function fetchTechnicalAnalysis(ticker) {
    const res = await callTechnical({ ticker });
    return res.data;
}

export async function fetchFundamentalAnalysis(ticker) {
    const res = await callFundamental({ ticker });
    return res.data;
}
