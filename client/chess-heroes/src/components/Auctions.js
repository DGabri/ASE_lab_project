import { useState, useEffect, useContext } from 'react'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Button from 'react-bootstrap/Button'
import Card from 'react-bootstrap/Card'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import goldIcon from '../assets/gold-icon.svg'
import getRunnningAuctions from '../services/getRunningAuctions'
import getPieces from '../services/getPieces'
import Form from 'react-bootstrap/Form'
import addBid from '../services/addBid'
import { UserContext } from '../App'
import { useNavigate } from 'react-router-dom'

const Auctions = ({ showAlert, refillUserGold }) => {
    const [runningAuctions, setRunningAuctions] = useState([])
    const [auctionPieces, setAuctionPieces] = useState({})
    const [bid, setBid] = useState()
    const user = useContext(UserContext)
    const navigate = useNavigate()

    const [filter, setFilter] = useState({
        "king": false,
        "queen": false,
        "knight": false,
        "rook": false,
        "bishop": false,
        "pawn": false,
    })

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
            getRunnningAuctions(user.access_token).then(res => {
                setRunningAuctions(res)

                if (res.length != 0) {
                    const pieces_id = res.map(auction => auction.piece_id)

                    getPieces(user.access_token, pieces_id).then(res => {
                        const pieces = res.reduce((pieces, piece) => {
                            pieces[piece.id] = piece
                            return pieces
                        }, {})

                        setAuctionPieces(pieces)
                    }).catch(error => showAlert("danger", error.toString()))
                }
            }).catch(error => showAlert("danger", error.toString()))
        }
    }, [user.logged])

    const makeBid = (auction) => {
        if (!isInteger(bid)) {
            setBid()
            showAlert("warning", "Invalid amount of gold.")
            return
        }

        if (parseInt(bid) <= auction.current_price) {
            setBid()
            showAlert("warning", "The bid must be greater than the current one.")
            return
        }

        if (parseInt(bid) > user.gold) {
            setBid()
            showAlert("warning", "You have insufficient gold.")
            return
        }

        addBid(user.access_token, user.id, auction.auction_id, parseInt(bid)).then(() => {
            showAlert("primary", "Bid added.")
            window.location.reload(false)
        }).catch(error => showAlert("danger", error.toString()))
    }

    const isInteger = (value) => {
        return Number.isInteger(value) || (typeof value === "string" && /^-?\d+$/.test(value) && !isNaN(parseInt(value, 10)))
    }
    
    return <>
        <div className="position-absolute m-5 z-1 p-2">
            <Card className="d-inline-block w-auto" body>
                {user.gold}
                <img width="20" className="ms-2" src={goldIcon} />
            </Card>
            <Button className="ms-3" variant="secondary" onClick={refillUserGold}>+</Button>
        </div>
        <div className="position-absolute end-0 m-5 p-3">
            <Button variant="primary" onClick={() => navigate("/auctions/create")}>Add an auction</Button>
        </div>
        <div className="d-flex justify-content-center"> 
            <Card className="my-5 w-auto" body>
                <Row>
                    {Object.keys(piecesImage).map(pic => (
                        <Col>
                            <img width="50" onClick={() => setFilter(prev => ({
                                ...prev,
                                [pic]: !filter[pic]
                            }))} className={`${filter[pic] ? "" : "opacity-50"}`} src={piecesImage[pic]} />
                        </Col>
                    ))}
                </Row>
            </Card>
        </div>
        <Container className="px-5">
            <Row className="d-flex justify-content-center">
                {runningAuctions.filter(auction => {
                    if (Object.values(filter).every(image => !image)) return true
                    const pieceImage = auctionPieces[auction.piece_id].pic
                    return filter[pieceImage]
                }).map(auction => (
                    <Col className="mb-4 col-auto">
                        <Card className="d-flex align-items-center p-2" style={{width: "18rem"}}>
                            <Card.Img className="my-3" src={piecesImage[auctionPieces[auction.piece_id]?.pic]} style={{height: "150px", width: "150px", backgroundSize: "contain"}} />
                            <h4 className="text-center">{auctionPieces[auction.piece_id]?.name}</h4>
                            <Card.Body className="d-flex flex-column justify-content-center">
                                <Card.Text className="text-center">
                                    <h6>Current: {auction.current_price}</h6>
                                </Card.Text>
                                {auction.seller_id == user.id && <Button variant="secondary" active>
                                    Your auction
                                </Button>}
                                {auction.best_bidder_id == user.id && <Button variant="primary" active>
                                    Already bidded
                                </Button>}
                                {auction.seller_id != user.id && auction.best_bidder_id != user.id && <Row>
                                    <Col className="col-auto">
                                        <Form.Control placeholder="0" value={bid} onChange={(e) => setBid(e.target.value)} style={{width: "5rem"}} />
                                    </Col>
                                    <Col className="col-auto">
                                        <Button variant="primary" onClick={() => makeBid(auction)}>Bid</Button>
                                    </Col>
                                </Row>}
                            </Card.Body>
                        </Card>
                    </Col>
                ))}
            </Row>
        </Container>
    </>
}

export default Auctions