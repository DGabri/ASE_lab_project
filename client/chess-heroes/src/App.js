import React, { useState, useEffect, createContext } from 'react'
import { Route, Routes, useNavigate, Link } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Navbar from 'react-bootstrap/Navbar'
import chessHeroesIcon from './assets/chess-heroes-icon.png'
import Home from './components/Home'
import Pieces from './components/Pieces'
import Banners from './components/Banners'
import Auctions from './components/Auctions'
import Account from './components/Account'
import Col from 'react-bootstrap/Col'
import defaultUserIcon from './assets/default-user-icon.svg'
import Login from './components/Login'
import userIcon from './assets/user-icon.svg'
import { getCookie, eraseCookie } from './utils/cookie'
import Dropdown from 'react-bootstrap/Dropdown'
import Register from './components/Register'
import Alert from 'react-bootstrap/Alert'
import logout from './services/logout'
import updateUserGold from './services/updateUserGold'
import getUserGold from './services/getUserGold'
import AuctionsCreate from './components/AuctionsCreate'
import './App.css'

export const UserContext = createContext({
    logged: false,
    access_token: "",
    id: 0,
    username: "",
    gold: 0,
    pic: defaultUserIcon,
    collection: {}
})

const App = () => {
    const [user, setUser] = useState({
        logged: false,
        access_token: "",
        id: 0,
        username: "",
        gold: 0,
        pic: defaultUserIcon,
        collection: {}
    })
    
    const [timeoutId, setTimeoutId] = useState(0)
    const navigate = useNavigate()

    const [alert, setAlert] = useState({
        display: false,
        type: "",
        message: ""
    })

    useEffect(() => {
        const access_token = getCookie("access_token")
        const user_id = getCookie("user_id")
        const username = getCookie("username")

        if (access_token && user_id && username) {
            getUserGold(access_token, user_id).then(res => {
                setUser(prev => ({
                    ...prev,
                    gold: res
                }))
            }).catch(error => showAlert("danger", error.toString()))

            setUser(prev => ({
                ...prev,
                logged: true,
                access_token: access_token,
                id: user_id,
                username: username,
                pic: userIcon
            }))
        }
    }, [])

    const makeLogout = () => {
        // logout(user.access_token, user.id).catch(error => showAlert("danger", error.toString())) 
        eraseCookie("access_token")
        eraseCookie("user_id")
        eraseCookie("username")

        setUser({
            logged: false,
            access_token: "",
            id: 0,
            username: "",
            gold: 0,
            pic: defaultUserIcon,
            collection: {}
        }) 
        
        showAlert("primary", "Logout successful")
        navigate("/")
    }

    const showAlert = (type, message) => {
        clearTimeout(timeoutId)

        setAlert({
            display: true,
            type: type,
            message: message
        })

        setTimeoutId(
            setTimeout(() => {
                setAlert({
                    display: false,
                    type: "",
                    message: ""
                })
            }, 5000)
        )
    }

    const refillUserGold = () => {
        updateUserGold(user.id, user.access_token, 10).then(res => {
            setUser(prev => ({
                ...prev,
                gold: res
            }))
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <UserContext.Provider value={user}>
        <div data-bs-theme="dark" className="bg-dark-subtle" style={{minHeight: "100vh"}}>
            <Navbar className="bg-body-tertiary z-1">
                <Container>
                    <Navbar.Brand>
                        <Link to="/" className="text-decoration-none">
                            <Container className="d-flex gap-3">
                                <Col>
                                    <img src={chessHeroesIcon} width="35" height="35"/>
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
                            <Dropdown>
                                <Dropdown.Toggle  id="account-icon" className="border-0" style={{backgroundColor: "transparent"}}>
                                    <img src={user.pic} width="45" height="45" />
                                </Dropdown.Toggle>
                                <Dropdown.Menu align="end">
                                    {user.logged && <Dropdown.Item onClick={makeLogout}>Logout</Dropdown.Item>}
                                    {!user.logged && <>
                                        <Dropdown.Item onClick={() => navigate("/login")}>Login</Dropdown.Item>
                                        <Dropdown.Item onClick={() => navigate("/register")}>Register</Dropdown.Item>
                                    </>}                                    
                                </Dropdown.Menu>
                                </Dropdown>
                        </Navbar.Text>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
            {alert.display && <div className="start-50 position-fixed my-4 z-1 translate-middle-x">
                <Alert key={alert.type} variant={alert.type}>
                    {alert.message}
                </Alert>
            </div>}
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/pieces" element={<Pieces
                    showAlert = {showAlert}
                />} />
                <Route path="/banners" element={<Banners
                    showAlert = {showAlert}
                    setUser = {setUser}
                    refillUserGold = {refillUserGold}
                />} />
                <Route path="/auctions" element={<Auctions
                    showAlert = {showAlert}
                    refillUserGold = {refillUserGold}
                />} />
                <Route path="/auctions/create" element={<AuctionsCreate
                    setUser = {setUser}
                    showAlert = {showAlert}
                    refillUserGold = {refillUserGold}
                />} />
                <Route path="/account" element={<Account
                    setUser = {setUser}
                    showAlert = {showAlert}
                />} />
                <Route path="/login" element={<Login
                    setUser = {setUser}
                    showAlert = {showAlert}
                />} />
                <Route path="/register" element={<Register
                    showAlert= {showAlert}
                />} />
            </Routes>
        </div>
    </UserContext.Provider>
}

export default App
