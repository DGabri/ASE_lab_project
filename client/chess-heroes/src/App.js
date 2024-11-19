import React, { useState } from 'react';
import { Route, Routes, useNavigate, useLocation } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Navbar from 'react-bootstrap/Navbar'
import icon from './assets/icon.png'
import Home from './components/Home'
import Pieces from './components/Pieces'
import Banners from './components/Banners'
import Auctions from './components/Auctions'
import Account from './components/Account'
import Profile from './components/Profile'
import './App.css'

const App = () => (
    <div data-bs-theme="dark" className="bg-dark-subtle">
        <Navbar className="bg-body-tertiary">
            <Container>
                <Navbar.Brand href="#home">
                    <img src={icon} width="30" className="d-inline-block align-top" />{' '}
                    Chess Heroes
                </Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    <Navbar.Text>
                    Signed in as: <a href="#login">Mark Otto</a>
                    </Navbar.Text>
                </Navbar.Collapse>
            </Container>
        </Navbar>
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/pieces" element={<Pieces />} />
            <Route path="/banners" element={<Banners />} />
            <Route path="/auctions" element={<Auctions />} />
            <Route path="/account" element={<Account />} />
            <Route path="/profile" element={<Profile />} />
        </Routes>
    </div>
)

export default App
