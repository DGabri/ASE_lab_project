import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Card from 'react-bootstrap/Card'
import login from '../services/login'
import userIcon from '../assets/user-icon.svg'
import getUserGold from '../services/getUserGold'
import { setCookie } from '../utils/cookie'

const Login = ({ setUser, showAlert }) => {
    const [username, setUsername] = useState("player")
    const [password, setPassword] = useState("ChessHeroes2024@")
    const navigate = useNavigate()

    const handleSubmit = (event) => {
        event.preventDefault()
        
        login(username, password).then(res => {
            const expire_days = (res.expires_in / 60) / 24
            const access_token = res.access_token
            const user_id = res.user.id
            const username = res.user.username
            setCookie("access_token", access_token, expire_days)
            setCookie("user_id", user_id, expire_days)
            setCookie("username", username, expire_days)

            getUserGold(access_token, user_id).then(res => {
                setUser(prev => ({
                    ...prev,
                    logged: true,
                    access_token: access_token,
                    id: user_id,
                    username: username,
                    pic: userIcon,
                    gold: res
                }))
            }).catch(error => showAlert("danger", error.toString()))

            
            showAlert("primary", "Login successful")
            navigate("/")
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <Container className="d-flex align-items-center justify-content-center position-absolute top-50 start-50 translate-middle">
        <Card className="d-inline-block w-auto h-auto p-5 mt-5">
            <h1 className="mb-5">Login</h1>
            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4" controlId="formUsername">
                    <Form.Label>Username</Form.Label>
                    <Form.Control type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-5" controlId="formPassword">
                    <Form.Label>Password</Form.Label>
                    <Form.Control type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </Form.Group>
                <Button variant="primary" type="submit">Login</Button>
            </Form>
        </Card>
    </Container>
}

export default Login