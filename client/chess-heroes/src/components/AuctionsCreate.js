import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import { useState, useEffect, useContext } from 'react'
import Button from 'react-bootstrap/Button'
import Card from 'react-bootstrap/Card'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import goldIcon from '../assets/gold-icon.svg'
import Form from 'react-bootstrap/Form'
import Dropdown from 'react-bootstrap/Dropdown'
import addAuction from '../services/addAuction'
import getPieces from '../services/getPieces'
import getUserCollection from '../services/getUserCollection'
import { UserContext } from '../App'
import { useNavigate } from 'react-router-dom'

const AuctionsCreate = ({ setUser, showAlert, refillUserGold }) => {
    const [userPieces, setUserPieces] = useState([])
    const [price, setPrice] = useState(10)
    const [duration, setDuration] = useState(1)
    const [selectedPiece, setSelectedPiece] = useState({})
    const user = useContext(UserContext)
    const navigate = useNavigate()

    const piecesImage = {
        "king": kingWhite,
        "queen": queenWhite,
        "knight": knightWhite,
        "rook": rookWhite,
        "bishop": bishopWhite,
        "pawn": pawnWhite,
    }

    useEffect(() => {
        if (user.logged) {
            getUserCollection(user.id, user.access_token).then(res => {
                setUser(prev => ({
                    ...prev,
                    collection: res
                }))

                getPieces(user.access_token, Object.keys(res)).then(res => {
                    setUserPieces(res)
                    setSelectedPiece(res[0])
                }).catch(error => showAlert("danger", error.toString()))
            }).catch(error => showAlert("danger", error.toString()))
        }
    }, [user.logged])

    const handleSubmit = (event) => {
        event.preventDefault()

        const auction = {
            "piece_id": selectedPiece.id,
            "seller_id": user.id,
            "start_price": price,
            "duration_hours": duration
        }

        addAuction(user.access_token, auction).then(() => {
            showAlert("primary", "Auction created.")
            navigate("/auctions")
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <>
        <div className="position-absolute m-5 z-1 p-2">
            <Card className="d-inline-block w-auto" body>
                {user.gold}
                <img width="20" className="ms-2" src={goldIcon} />
            </Card>
            <Button className="ms-3" variant="secondary" onClick={refillUserGold}>+</Button>
        </div>
        <Container className="d-flex align-items-center justify-content-center position-absolute top-50 start-50 translate-middle mt-5">
            <Card className="d-flex align-items-center p-2">
                <Card.Img className="my-3" src={piecesImage[selectedPiece.pic]} style={{height: "150px", width: "150px", backgroundSize: "contain"}} />
                <Card.Body className="d-flex flex-column justify-content-center align-items-center gap-5">
                    <Dropdown>
                        <Dropdown.Toggle variant="secondary">
                            {selectedPiece.name}
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            {Object.entries(user.collection).map(([pieceId, copies]) => {
                                const piece = userPieces.filter(piece => piece.id == pieceId)[0]
                                return <Dropdown.Item onClick={() => setSelectedPiece(piece)}>{piece?.name} {copies}x</Dropdown.Item>
                            })}
                        </Dropdown.Menu>
                    </Dropdown>
                    <Form onSubmit={handleSubmit} className="d-flex flex-column">
                        <Row>
                            <Col>
                            <Form.Group className="mb-4" style={{width: "7.5rem"}}>
                                <Form.Label>Price</Form.Label>
                                <Form.Control type="text" value={price} onChange={(e) => setPrice(e.target.value)} />
                            </Form.Group></Col><Col>
                            <Form.Group className="mb-5" style={{width: "7.5rem"}}>
                                <Form.Label>Duration hours</Form.Label>
                                <Form.Control type="text"value={duration} onChange={(e) => setDuration(e.target.value)} />
                            </Form.Group></Col>
                        </Row>
                        <Button variant="primary" type="submit">Create</Button>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    </>
}

export default AuctionsCreate