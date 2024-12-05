import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Card from 'react-bootstrap/Card'
import register from '../services/register'

const Register = ({ showAlert }) => {
    const [email, setEmail] = useState("")
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = (event) => {
        event.preventDefault()
        
        register(email, username, password).then(() => {
            showAlert("primary", "Registration successful")
            navigate("/")
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <Container className="d-flex align-items-center justify-content-center position-absolute top-50 start-50 translate-middle">
        <Card className="d-inline-block w-auto h-auto p-5 mt-5">
            <h1 className="mb-5">Register</h1>
            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4">
                    <Form.Label>Email</Form.Label>
                    <Form.Control type="email" placeholder="Password" value={email} onChange={(e) => setEmail(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-4">
                    <Form.Label>Username</Form.Label>
                    <Form.Control type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-5">
                    <Form.Label>Password</Form.Label>
                    <Form.Control type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </Form.Group>
                <Button variant="primary" type="submit">Register</Button>
            </Form>
        </Card>
    </Container>
}

export default Register