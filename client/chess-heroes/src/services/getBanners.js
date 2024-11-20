const getBanners = async () => {
    const responses = []
    responses.push((await fetch("http://127.0.0.1:5004/banner/1").then(res => res.json()))["banner"])
    responses.push((await fetch("http://127.0.0.1:5004/banner/2").then(res => res.json()))["banner"])
    responses.push((await fetch("http://127.0.0.1:5004/banner/3").then(res => res.json()))["banner"])
    return responses
}

export default getBanners