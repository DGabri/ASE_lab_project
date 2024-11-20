import React, { useState } from 'react';
import { Route, Routes, useNavigate, useLocation, Link } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Navbar from 'react-bootstrap/Navbar'
import chessHeroesIcon from './assets/chess-heroes-icon.png'
import Home from './components/Home'
import Pieces from './components/Pieces'
import Banners from './components/Banners'
import Auctions from './components/Auctions'
import Account from './components/Account'
import Profile from './components/Profile'
import Col from 'react-bootstrap/Col'
import './App.css'

const App = () => (
    <div data-bs-theme="dark" className="bg-dark-subtle">
        <Navbar className="bg-body-tertiary">
            <Container>
                <Navbar.Brand>
                    <Link to="/" className="text-decoration-none">
                        <Container className="d-flex gap-3">
                            <Col>
                                <img src={chessHeroesIcon} width="30" height="30"/>
                            </Col>
                            <Col className="d-flex align-items-center">
                                <h5 className="m-0 text-white">Chess Heroes</h5>
                            </Col>
                        </Container>
                    </Link>
                </Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end gap-5">
                    <Navbar.Text>
                        <Link to="/pieces" className="text-decoration-none">
                            <h5 className="m-0">Pieces</h5>
                        </Link>
                    </Navbar.Text>
                    <Navbar.Text>
                        <Link to="/banners" className="text-decoration-none">
                            <h5 className="m-0">Banners</h5>
                        </Link>
                    </Navbar.Text>
                    <Navbar.Text>
                        <Link to="/auctions" className="text-decoration-none">
                            <h5 className="m-0">Auctions</h5>
                        </Link>
                    </Navbar.Text>
                    <Navbar.Text>
                        <Link to="/account" className="text-decoration-none">
                            <h5 className="m-0">Account</h5>
                        </Link>
                    </Navbar.Text>
                    <Navbar.Text>
                        <Link to="/profile" className="text-decoration-none">
                            <h5 className="m-0">Profile</h5>
                        </Link>
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
