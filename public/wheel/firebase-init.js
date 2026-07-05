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
    getFirestore,
    doc,
    getDoc,
    setDoc,
    onSnapshot,
    enableIndexedDbPersistence
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js?v=6";

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// Permite que o app funcione offline (cache local) enquanto sincroniza com o Firestore.
enableIndexedDbPersistence(db).catch(() => {
    // Falha silenciosa: acontece com múltiplas abas abertas ou navegadores sem suporte.
});

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

function userDocRef(uid) {
    return doc(db, 'users', uid, 'wheelData', 'state');
}

export async function fetchUserState(uid) {
    const snap = await getDoc(userDocRef(uid));
    return snap.exists() ? snap.data() : null;
}

export function saveUserState(uid, state) {
    return setDoc(userDocRef(uid), state);
}

export function subscribeUserState(uid, callback) {
    return onSnapshot(userDocRef(uid), (snap) => {
        if (snap.exists()) callback(snap.data());
    });
}
